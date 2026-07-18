from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import contains_eager, joinedload

from app.config import settings
from app.database.advisory_lock import distributed_job_lock
from app.database.database import AsyncSessionLocal
from app.database.models import Subscription, SubscriptionStatus, Tariff, User
from app.external.remnawave_api import RemnaWaveAPIError, RemnaWaveUser, UserStatus
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
_METERED_TRAFFIC_PAGE_SIZE = 1000
_METERED_TRAFFIC_WORKER_CONCURRENCY = 8
_METERED_TRAFFIC_MIN_LOOP_DELAY_SECONDS = 5.0
_METERED_TRAFFIC_USER_TIMEOUT_SECONDS = 75.0


@dataclass
class MeteredTrafficRunStats:
    scanned: int = 0
    candidates: int = 0
    checked: int = 0
    initialized: int = 0
    warned: int = 0
    blocked: int = 0
    restored: int = 0
    reconciled: int = 0
    errors: int = 0
    deferred: int = 0
    skipped: bool = False
    aborted: bool = False
    pages: int = 0
    duration_seconds: float = 0.0


@dataclass
class _MeteredTrafficPageResult:
    results: list[tuple[RemnaWaveUser, dict[str, bool] | None, Exception | None]]
    deferred: int = 0
    circuit_open: bool = False


@dataclass
class _MeteredTrafficFastPathResult:
    results: list[tuple[RemnaWaveUser, dict[str, bool] | None, Exception | None]]
    slow_users: list[RemnaWaveUser]
    candidates: int = 0
    deferred: int = 0


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
            iteration_started = time.monotonic()
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except RemnaWaveAPIError as error:
                self._last_error = str(error)
                # The API client logs the root transport/HTTP failure once. The monitor
                # retries on the next interval, so reporting the wrapper as another
                # ERROR only produces duplicate administrator notifications.
                logger.warning('Metered traffic monitor iteration deferred', error=error)
            except Exception as error:
                self._last_error = str(error)
                logger.error('Metered traffic monitor iteration failed', error=error, exc_info=True)
            elapsed = time.monotonic() - iteration_started
            await asyncio.sleep(self._calculate_loop_delay(get_metered_check_interval_seconds(), elapsed))

    @staticmethod
    def _calculate_loop_delay(interval_seconds: int, elapsed_seconds: float) -> float:
        """Keep a stable start-to-start cadence without spinning after an overrun."""
        interval = max(1.0, float(interval_seconds))
        minimum_delay = min(_METERED_TRAFFIC_MIN_LOOP_DELAY_SECONDS, interval)
        return max(minimum_delay, interval - max(0.0, elapsed_seconds))

    async def run_once(self) -> MeteredTrafficRunStats:
        stats = MeteredTrafficRunStats()
        run_started = time.monotonic()
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
                    async for panel_users in self._iter_panel_user_pages(api):
                        stats.pages += 1
                        stats.scanned += len(panel_users)
                        fast_path = await self._process_panel_users_fast_path(panel_users)
                        stats.candidates += fast_path.candidates
                        stats.deferred += fast_path.deferred
                        self._record_results(stats, fast_path.results)

                        page_result = await self._process_panel_users_concurrently(
                            api,
                            fast_path.slow_users,
                        )
                        self._record_results(stats, page_result.results)

                        if page_result.circuit_open:
                            stats.deferred += page_result.deferred
                            stats.aborted = True
                            logger.warning(
                                'Metered traffic monitor circuit opened after systemic failures',
                                deferred=page_result.deferred,
                            )
                            break
            except Exception as error:
                stats.errors += 1
                self._last_error = str(error)
                raise
            finally:
                stats.duration_seconds = round(time.monotonic() - run_started, 3)
                self._last_run_at = datetime.now(UTC)
                self._last_stats = stats

        self._last_error = (
            'Проверка остановлена после серии системных ошибок; оставшиеся подписки будут повторены в следующем проходе'
            if stats.aborted
            else None
        )
        logger.info('Metered traffic monitor completed', **asdict(stats))
        return stats

    @staticmethod
    def _record_results(
        stats: MeteredTrafficRunStats,
        results: list[tuple[RemnaWaveUser, dict[str, bool] | None, Exception | None]],
    ) -> None:
        for panel_user, result, error in results:
            if error is not None:
                stats.errors += 1
                logger.error(
                    'Failed to process metered traffic user',
                    panel_user_uuid=panel_user.uuid,
                    error=error,
                    exc_info=(type(error), error, error.__traceback__),
                )
                continue
            if result is None:
                continue
            stats.checked += 1
            for key in ('initialized', 'warned', 'blocked', 'restored', 'reconciled'):
                if result.get(key):
                    setattr(stats, key, getattr(stats, key) + 1)

    @staticmethod
    async def _validate_node_multipliers(api) -> list[str]:
        configured = get_metered_node_multipliers()
        nodes = await api.get_all_nodes()
        nodes_by_uuid = {node.uuid: node for node in nodes}
        errors: list[str] = []

        missing = set(configured) - nodes_by_uuid.keys()
        if missing:
            errors.append(f'Не найдены ноды: {", ".join(sorted(missing))}')

        corrections: dict[float, list[str]] = {}
        correction_names: dict[float, list[str]] = {}
        for node in nodes:
            multiplier = float(node.consumption_multiplier or 0)
            expected = configured.get(node.uuid, 0.0)
            if abs(multiplier - expected) > 0.001:
                corrections.setdefault(expected, []).append(node.uuid)
                correction_names.setdefault(expected, []).append(node.name)

        for expected, node_uuids in corrections.items():
            updated = await api.update_nodes_consumption_multiplier(node_uuids, expected)
            if not updated:
                errors.append(
                    f'Не удалось установить коэффициент {expected:g} для нод: {", ".join(correction_names[expected])}'
                )
                continue
            logger.info(
                'Metered traffic node multipliers reconciled',
                node_uuids=node_uuids,
                node_names=correction_names[expected],
                multiplier=expected,
            )

        return errors

    @staticmethod
    async def _iter_panel_user_pages(api) -> AsyncIterator[list[RemnaWaveUser]]:
        start = 0
        while True:
            page = await api.get_all_users(
                start=start,
                size=_METERED_TRAFFIC_PAGE_SIZE,
                enrich_happ_links=False,
            )
            batch = page['users']
            if batch:
                yield batch
            start += len(batch)
            if not batch or start >= int(page['total']):
                break

    async def _process_panel_users_fast_path(
        self,
        panel_users: list[RemnaWaveUser],
    ) -> _MeteredTrafficFastPathResult:
        """Update healthy subscriptions in one short transaction per panel page."""
        if not panel_users:
            return _MeteredTrafficFastPathResult(results=[], slow_users=[])

        panel_users_by_uuid = {panel_user.uuid: panel_user for panel_user in panel_users}
        now = datetime.now(UTC)
        async with AsyncSessionLocal() as db:
            active_query = (
                select(User.remnawave_uuid)
                .join(Subscription, Subscription.user_id == User.id)
                .where(
                    User.remnawave_uuid.in_(panel_users_by_uuid),
                    Subscription.status.in_((SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value)),
                    Subscription.end_date > now,
                )
            )
            active_uuids = set((await db.scalars(active_query)).all())
            if not active_uuids:
                return _MeteredTrafficFastPathResult(results=[], slow_users=[])

            subscription_query = (
                select(Subscription)
                .join(User, User.id == Subscription.user_id)
                .options(*self._subscription_load_options())
                .where(
                    User.remnawave_uuid.in_(active_uuids),
                    Subscription.status.in_((SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value)),
                    Subscription.end_date > now,
                )
                .with_for_update(of=Subscription, skip_locked=True)
            )
            subscriptions = (await db.execute(subscription_query)).scalars().all()
            subscriptions_by_uuid = {
                subscription.user.remnawave_uuid: subscription
                for subscription in subscriptions
                if subscription.user.remnawave_uuid
            }

            results: list[tuple[RemnaWaveUser, dict[str, bool] | None, Exception | None]] = []
            slow_users: list[RemnaWaveUser] = []
            for panel_user in panel_users:
                subscription = subscriptions_by_uuid.get(panel_user.uuid)
                if subscription is None:
                    continue
                if self._requires_individual_processing(subscription, panel_user):
                    slow_users.append(panel_user)
                    continue
                results.append(
                    (
                        panel_user,
                        self._apply_fast_path(subscription, panel_user, now=now),
                        None,
                    )
                )

            await db.commit()

        return _MeteredTrafficFastPathResult(
            results=results,
            slow_users=slow_users,
            candidates=len(active_uuids),
            deferred=max(0, len(active_uuids) - len(subscriptions)),
        )

    @staticmethod
    def _subscription_load_options() -> tuple[Any, Any]:
        return (
            contains_eager(Subscription.user).load_only(
                User.id,
                User.telegram_id,
                User.status,
                User.language,
                User.remnawave_uuid,
                User.email,
                User.email_verified,
                User.notification_settings,
            ),
            joinedload(Subscription.tariff).load_only(
                Tariff.id,
                Tariff.special_servers_enabled,
            ),
        )

    def _requires_individual_processing(
        self,
        subscription: Subscription,
        panel_user: RemnaWaveUser,
    ) -> bool:
        panel_squads = extract_squad_uuids(panel_user.active_internal_squads)
        stored_squads = extract_squad_uuids(subscription.connected_squads)
        if panel_user.traffic_limit_bytes != 0 or panel_user.status == UserStatus.LIMITED:
            return True

        if not subscription_allows_special_servers(subscription):
            desired_squads = build_subscription_squads(subscription)
            return set(panel_squads) != set(desired_squads)

        if set(panel_squads) != set(stored_squads):
            return True

        metered_squads = get_metered_squad_uuids()
        has_all_metered_squads = all(squad_uuid in stored_squads for squad_uuid in metered_squads)
        is_blocked = bool(subscription.metered_access_blocked)

        if subscription.metered_traffic_initialized_at is None:
            return is_blocked or not has_all_metered_squads

        panel_counter = max(0, int(panel_user.used_traffic_bytes or 0))
        used_bytes, _, _ = calculate_metered_usage(
            panel_counter_bytes=panel_counter,
            baseline_bytes=subscription.metered_traffic_baseline_bytes,
            last_counter_bytes=subscription.metered_traffic_last_counter_bytes,
        )
        limit_bytes = max(0, int(subscription.traffic_limit_gb or 0)) * BYTES_PER_GB
        if limit_bytes <= 0:
            return is_blocked or not has_all_metered_squads

        if used_bytes >= limit_bytes:
            had_entitlement = any(squad_uuid in stored_squads for squad_uuid in metered_squads) or is_blocked
            if had_entitlement:
                return not is_blocked or any(squad_uuid in stored_squads for squad_uuid in metered_squads)
        elif is_blocked or not has_all_metered_squads:
            return True

        actual_percent = int((used_bytes * 100) / limit_bytes)
        warning_percent = self._resolve_user_warning_percent(subscription.user)
        return actual_percent >= warning_percent and subscription.metered_warning_percent < warning_percent

    @staticmethod
    def _apply_fast_path(
        subscription: Subscription,
        panel_user: RemnaWaveUser,
        *,
        now: datetime,
    ) -> dict[str, bool]:
        result = {
            'initialized': False,
            'warned': False,
            'blocked': False,
            'restored': False,
            'reconciled': False,
        }
        panel_counter = max(0, int(panel_user.used_traffic_bytes or 0))

        if not subscription_allows_special_servers(subscription):
            disable_metered_access(subscription, panel_counter_bytes=panel_counter)
            return result

        if subscription.metered_traffic_initialized_at is None:
            subscription.metered_traffic_baseline_bytes = panel_counter
            subscription.metered_traffic_last_counter_bytes = panel_counter
            subscription.metered_traffic_initialized_at = now
            subscription.metered_traffic_last_checked_at = now
            subscription.metered_warning_percent = 0
            subscription.traffic_used_gb = 0.0
            result['initialized'] = True
            return result

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

        limit_bytes = max(0, int(subscription.traffic_limit_gb or 0)) * BYTES_PER_GB
        if limit_bytes > 0 and used_bytes >= limit_bytes and subscription.metered_access_blocked:
            block_metered_access(subscription)

        return result

    async def _process_panel_users_concurrently(
        self,
        api,
        panel_users: list[RemnaWaveUser],
    ) -> _MeteredTrafficPageResult:
        async def process_one(
            panel_user: RemnaWaveUser,
        ) -> tuple[RemnaWaveUser, dict[str, bool] | None, Exception | None]:
            try:
                async with asyncio.timeout(_METERED_TRAFFIC_USER_TIMEOUT_SECONDS):
                    return panel_user, await self._process_panel_user(api, panel_user), None
            except asyncio.CancelledError:
                raise
            except Exception as error:
                return panel_user, None, error

        results: list[tuple[RemnaWaveUser, dict[str, bool] | None, Exception | None]] = []
        for offset in range(0, len(panel_users), _METERED_TRAFFIC_WORKER_CONCURRENCY):
            chunk = panel_users[offset : offset + _METERED_TRAFFIC_WORKER_CONCURRENCY]
            chunk_results = await asyncio.gather(*(process_one(panel_user) for panel_user in chunk))
            results.extend(chunk_results)

            if len(chunk) == _METERED_TRAFFIC_WORKER_CONCURRENCY and all(
                error is not None and self._is_systemic_error(error) for _, _, error in chunk_results
            ):
                return _MeteredTrafficPageResult(
                    results=results,
                    deferred=len(panel_users) - len(results),
                    circuit_open=True,
                )

        return _MeteredTrafficPageResult(results=results)

    @staticmethod
    def _is_systemic_error(error: Exception) -> bool:
        if isinstance(error, (TimeoutError, OperationalError, InterfaceError)):
            return True
        if isinstance(error, RemnaWaveAPIError):
            return error.status_code is None or error.status_code == 429 or error.status_code >= 500
        return False

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
                .options(*self._subscription_load_options())
                .where(User.remnawave_uuid == panel_user.uuid)
                .with_for_update(of=Subscription)
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
                any(squad_uuid in connected_squads for squad_uuid in squad_uuids) or subscription.metered_access_blocked
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
