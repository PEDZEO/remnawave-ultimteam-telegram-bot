from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.advisory_lock import distributed_job_lock
from app.database.database import AsyncSessionLocal
from app.database.models import Subscription, User
from app.external.remnawave_api import RemnaWaveUser, UserStatus
from app.localization.texts import get_texts
from app.services.metered_traffic_policy import (
    BYTES_PER_GB,
    block_metered_access,
    build_subscription_squads,
    calculate_metered_usage,
    disable_metered_access,
    extract_squad_uuids,
    get_metered_check_interval_seconds,
    get_metered_node_multipliers,
    get_metered_node_uuids,
    get_metered_squad_uuid,
    get_metered_squad_uuids,
    get_metered_warning_percent,
    is_metered_traffic_enabled,
    restore_metered_access_if_available,
    subscription_allows_special_servers,
)
from app.services.notification_delivery_service import NotificationType, notification_delivery_service
from app.services.remnawave_service import RemnaWaveService
from app.utils.miniapp_buttons import build_miniapp_or_callback_button


logger = structlog.get_logger(__name__)

_METERED_TRAFFIC_LOCK_ID = 7_612_946_175_504_209_054


@dataclass
class MeteredTrafficRunStats:
    checked: int = 0
    initialized: int = 0
    warned: int = 0
    blocked: int = 0
    restored: int = 0
    reconciled: int = 0
    errors: int = 0
    skipped: bool = False


class MeteredTrafficService:
    def __init__(self) -> None:
        self._bot: Bot | None = None
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_run_at: datetime | None = None
        self._last_error: str | None = None
        self._last_stats = MeteredTrafficRunStats()
        self._last_topology_errors: list[str] = []
        self._remnawave_service = RemnaWaveService()

    def set_bot(self, bot: Bot) -> None:
        self._bot = bot

    def is_enabled(self) -> bool:
        return is_metered_traffic_enabled()

    def get_status(self) -> dict[str, Any]:
        return {
            'enabled': self.is_enabled(),
            'running': self._task is not None and not self._task.done(),
            'squad_uuid': get_metered_squad_uuid(),
            'squad_uuids': get_metered_squad_uuids(),
            'node_uuids': get_metered_node_uuids(),
            'node_multipliers': get_metered_node_multipliers(),
            'interval_seconds': get_metered_check_interval_seconds(),
            'last_run_at': self._last_run_at.isoformat() if self._last_run_at else None,
            'last_error': self._last_error,
            'last_stats': asdict(self._last_stats),
            'topology_errors': self._last_topology_errors,
        }

    async def start(self) -> None:
        if not self.is_enabled() or (self._task and not self._task.done()):
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(), name='metered-traffic-monitor')
        logger.info(
            'Metered traffic monitor started',
            interval_seconds=get_metered_check_interval_seconds(),
            squad_uuids=get_metered_squad_uuids(),
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                self._last_error = str(error)
                logger.error('Metered traffic monitor iteration failed', error=error, exc_info=True)
            await asyncio.sleep(get_metered_check_interval_seconds())

    async def run_once(self) -> MeteredTrafficRunStats:
        stats = MeteredTrafficRunStats()
        if not self.is_enabled():
            stats.skipped = True
            return stats

        async with distributed_job_lock(_METERED_TRAFFIC_LOCK_ID, name='metered-traffic-monitor') as acquired:
            if not acquired:
                stats.skipped = True
                return stats

            try:
                async with self._remnawave_service.get_api_client() as api:
                    self._last_topology_errors = await self._validate_node_multipliers(api)
                    if self._last_topology_errors:
                        raise RuntimeError('; '.join(self._last_topology_errors))
                    panel_users = await self._load_panel_users(api)
                    for panel_user in panel_users:
                        try:
                            result = await self._process_panel_user(api, panel_user)
                            if result is None:
                                continue
                            stats.checked += 1
                            for key in ('initialized', 'warned', 'blocked', 'restored', 'reconciled'):
                                if result.get(key):
                                    setattr(stats, key, getattr(stats, key) + 1)
                        except Exception as error:
                            stats.errors += 1
                            logger.error(
                                'Failed to process metered traffic user',
                                panel_user_uuid=panel_user.uuid,
                                error=error,
                                exc_info=True,
                            )
            except Exception as error:
                stats.errors += 1
                self._last_error = str(error)
                raise
            finally:
                self._last_run_at = datetime.now(UTC)
                self._last_stats = stats

        self._last_error = None
        logger.info('Metered traffic monitor completed', **asdict(stats))
        return stats

    @staticmethod
    async def _validate_node_multipliers(api) -> list[str]:
        configured = get_metered_node_multipliers()
        nodes = await api.get_all_nodes()
        nodes_by_uuid = {node.uuid: node for node in nodes}
        errors: list[str] = []

        missing = set(configured) - nodes_by_uuid.keys()
        if missing:
            errors.append(f'Не найдены ноды: {", ".join(sorted(missing))}')

        for node in nodes:
            multiplier = float(node.consumption_multiplier or 0)
            expected = configured.get(node.uuid, 0.0)
            if abs(multiplier - expected) > 0.001:
                errors.append(f'Нода {node.name}: коэффициент {multiplier:g}, требуется {expected:g}')

        return errors

    @staticmethod
    async def _load_panel_users(api) -> list[RemnaWaveUser]:
        users: list[RemnaWaveUser] = []
        start = 0
        page_size = 100
        while True:
            page = await api.get_all_users(start=start, size=page_size, enrich_happ_links=False)
            batch = page['users']
            users.extend(batch)
            start += len(batch)
            if not batch or start >= int(page['total']):
                break
        return users

    async def _process_panel_user(self, api, panel_user: RemnaWaveUser) -> dict[str, bool] | None:
        now = datetime.now(UTC)
        notification: tuple[User, Subscription, bool, int] | None = None
        result = {
            'initialized': False,
            'warned': False,
            'blocked': False,
            'restored': False,
            'reconciled': False,
        }

        async with AsyncSessionLocal() as db:
            query = (
                select(Subscription)
                .join(User, User.id == Subscription.user_id)
                .options(selectinload(Subscription.user), selectinload(Subscription.tariff))
                .where(User.remnawave_uuid == panel_user.uuid)
                .with_for_update()
            )
            subscription = (await db.execute(query)).scalar_one_or_none()
            if subscription is None or subscription.end_date is None:
                return None
            if subscription.end_date <= now or subscription.actual_status not in {'active', 'trial'}:
                return None

            user = subscription.user
            panel_counter = max(0, int(panel_user.used_traffic_bytes or 0))
            if not subscription_allows_special_servers(subscription):
                disable_metered_access(subscription, panel_counter_bytes=panel_counter)
                desired_squads = build_subscription_squads(subscription)
                subscription.connected_squads = desired_squads
                current_squads = extract_squad_uuids(panel_user.active_internal_squads)
                needs_reconcile = set(current_squads) != set(desired_squads) or panel_user.traffic_limit_bytes != 0

                if needs_reconcile:
                    await api.update_user(
                        uuid=panel_user.uuid,
                        traffic_limit_bytes=0,
                        active_internal_squads=desired_squads,
                    )
                    result['reconciled'] = True

                if panel_user.status == UserStatus.LIMITED:
                    await api.enable_user(panel_user.uuid)
                    result['reconciled'] = True

                await db.commit()
                return result

            initialized = subscription.metered_traffic_initialized_at is not None

            if not initialized:
                subscription.metered_traffic_baseline_bytes = panel_counter
                subscription.metered_traffic_last_counter_bytes = panel_counter
                subscription.metered_traffic_initialized_at = now
                subscription.metered_traffic_last_checked_at = now
                subscription.metered_warning_percent = 0
                subscription.traffic_used_gb = 0.0
                used_bytes = 0
                result['initialized'] = True
            else:
                used_bytes, baseline, counter_was_reset = calculate_metered_usage(
                    panel_counter_bytes=panel_counter,
                    baseline_bytes=subscription.metered_traffic_baseline_bytes,
                    last_counter_bytes=subscription.metered_traffic_last_counter_bytes,
                )
                subscription.metered_traffic_baseline_bytes = baseline
                subscription.metered_traffic_last_counter_bytes = panel_counter
                subscription.metered_traffic_last_checked_at = now
                subscription.traffic_used_gb = round(used_bytes / BYTES_PER_GB, 6)
                if counter_was_reset:
                    subscription.metered_warning_percent = 0

            limit_gb = max(0, int(subscription.traffic_limit_gb or 0))
            limit_bytes = limit_gb * BYTES_PER_GB
            squad_uuids = get_metered_squad_uuids()
            connected_squads = extract_squad_uuids(subscription.connected_squads)
            had_metered_entitlement = (
                any(squad_uuid in connected_squads for squad_uuid in squad_uuids)
                or subscription.metered_access_blocked
            )

            transition_blocked = False
            transition_restored = False
            warning_percent = self._resolve_user_warning_percent(user)

            if limit_bytes <= 0:
                transition_restored = restore_metered_access_if_available(subscription)
            elif used_bytes >= limit_bytes and had_metered_entitlement:
                transition_blocked = not subscription.metered_access_blocked
                block_metered_access(subscription)
            else:
                transition_restored = restore_metered_access_if_available(subscription)
                actual_percent = int((used_bytes * 100) / limit_bytes) if limit_bytes else 0
                if actual_percent >= warning_percent and subscription.metered_warning_percent < warning_percent:
                    subscription.metered_warning_percent = warning_percent
                    notification = (user, subscription, False, actual_percent)
                    result['warned'] = True

            desired_squads = extract_squad_uuids(subscription.connected_squads)
            current_squads = extract_squad_uuids(panel_user.active_internal_squads)
            needs_reconcile = set(current_squads) != set(desired_squads) or panel_user.traffic_limit_bytes != 0

            if needs_reconcile:
                await api.update_user(
                    uuid=panel_user.uuid,
                    traffic_limit_bytes=0,
                    active_internal_squads=desired_squads,
                )
                result['reconciled'] = True

            if panel_user.status == UserStatus.LIMITED:
                await api.enable_user(panel_user.uuid)
                result['reconciled'] = True

            await db.commit()

            if transition_blocked:
                result['blocked'] = True
                notification = (user, subscription, True, 100)
            elif transition_restored:
                result['restored'] = True

        if notification:
            user, subscription, exhausted, actual_percent = notification
            await self._notify_user(user, subscription, exhausted=exhausted, actual_percent=actual_percent)

        return result

    @staticmethod
    def _resolve_user_warning_percent(user: User) -> int:
        notification_settings = user.notification_settings if isinstance(user.notification_settings, dict) else {}
        try:
            value = int(notification_settings.get('traffic_warning_percent', get_metered_warning_percent()))
        except (TypeError, ValueError):
            value = get_metered_warning_percent()
        return min(95, max(25, value))

    async def _notify_user(
        self,
        user: User,
        subscription: Subscription,
        *,
        exhausted: bool,
        actual_percent: int,
    ) -> None:
        notification_settings = user.notification_settings if isinstance(user.notification_settings, dict) else {}
        if not exhausted and notification_settings.get('traffic_warning_enabled') is False:
            return

        used_gb_value = max(0.0, float(subscription.traffic_used_gb or 0.0))
        limit_gb_value = max(0, int(subscription.traffic_limit_gb or 0))
        remaining_gb_value = max(0.0, limit_gb_value - used_gb_value)
        values = {
            'percent': actual_percent,
            'used_gb': self._format_gb(used_gb_value),
            'limit_gb': self._format_gb(float(limit_gb_value)),
            'remaining_gb': self._format_gb(remaining_gb_value),
        }

        if str(user.language or '').lower().startswith('ru'):
            template = (
                settings.ULTIMA_METERED_EXHAUSTED_MESSAGE_RU
                if exhausted
                else settings.ULTIMA_TRAFFIC_WARNING_MESSAGE_RU
            )
        elif exhausted:
            template = (
                '⚠️ <b>Special-server traffic is exhausted</b>\n\n'
                'Used {used_gb} of {limit_gb} GB. Special servers are temporarily unavailable, '
                'but standard unlimited VPN servers continue to work.'
            )
        else:
            template = (
                '📊 <b>Special-server traffic is almost exhausted</b>\n\n'
                'Used {percent}%: {used_gb} of {limit_gb} GB. Remaining: {remaining_gb} GB.'
            )

        try:
            message = str(template).format(**values)
        except (KeyError, ValueError):
            logger.error('Invalid metered traffic notification template; using fallback')
            message = (
                f'⚠️ <b>Трафик спецсерверов закончился</b>\n\nИспользовано '
                f'{values["used_gb"]} из {values["limit_gb"]} ГБ.'
                if exhausted
                else f'📊 <b>Трафик почти закончился</b>\n\nОсталось {values["remaining_gb"]} ГБ.'
            )

        texts = get_texts(user.language)
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    build_miniapp_or_callback_button(
                        text=texts.get('BUY_TRAFFIC_BUTTON', '📈 Докупить трафик'),
                        callback_data='buy_traffic',
                    )
                ],
                [
                    build_miniapp_or_callback_button(
                        text=texts.get('MY_SUBSCRIPTION_BUTTON', '📱 Моя подписка'),
                        callback_data='menu_subscription',
                    )
                ],
            ]
        )
        await notification_delivery_service.send_notification(
            user=user,
            notification_type=NotificationType.WEBHOOK_SUB_BANDWIDTH_THRESHOLD,
            context=values,
            bot=self._bot,
            telegram_message=message,
            telegram_markup=markup,
        )

    @staticmethod
    def _format_gb(value: float) -> str:
        return f'{value:.2f}'.rstrip('0').rstrip('.')


metered_traffic_service = MeteredTrafficService()
