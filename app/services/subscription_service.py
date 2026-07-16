from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.user import get_user_by_id
from app.database.models import PromoGroup, Subscription, SubscriptionStatus, User
from app.external.remnawave_api import RemnaWaveAPI, RemnaWaveAPIError, RemnaWaveUser, TrafficLimitStrategy, UserStatus
from app.services.metered_traffic_policy import (
    is_metered_traffic_enabled,
    panel_traffic_limit_bytes,
    reset_metered_cycle,
    restore_metered_access_if_available,
)
from app.utils.pricing_utils import (
    calculate_months_from_days,
    get_remaining_months,
)
from app.utils.subscription_utils import (
    resolve_hwid_device_limit_for_payload,
)


logger = structlog.get_logger(__name__)


def _resolve_discount_percent(
    user: User | None,
    promo_group: PromoGroup | None,
    category: str,
    *,
    period_days: int | None = None,
) -> int:
    if user is not None:
        try:
            return user.get_promo_discount(category, period_days)
        except AttributeError:
            pass

    if promo_group is not None:
        return promo_group.get_discount_percent(category, period_days)

    return 0


def _resolve_addon_discount_percent(
    user: User | None,
    promo_group: PromoGroup | None,
    category: str,
    *,
    period_days: int | None = None,
) -> int:
    group = promo_group or (user.get_primary_promo_group() if user else None)

    if group is not None and not getattr(group, 'apply_discounts_to_addons', True):
        return 0

    return _resolve_discount_percent(
        user,
        promo_group,
        category,
        period_days=period_days,
    )


def get_traffic_reset_strategy(tariff=None):
    """Получает стратегию сброса трафика.

    Args:
        tariff: Объект тарифа. Если у тарифа задан traffic_reset_mode,
               используется он, иначе глобальная настройка из конфига.

    Returns:
        TrafficLimitStrategy: Стратегия сброса трафика для RemnaWave API.
    """
    from app.config import settings

    strategy_mapping = {'NO_RESET': 'NO_RESET', 'DAY': 'DAY', 'WEEK': 'WEEK', 'MONTH': 'MONTH'}

    # Проверяем настройку тарифа
    if tariff is not None:
        tariff_mode = getattr(tariff, 'traffic_reset_mode', None)
        if tariff_mode is not None:
            mapped_strategy = strategy_mapping.get(tariff_mode.upper(), 'NO_RESET')
            logger.info(
                '🔄 Стратегия сброса трафика из тарифа',
                value=getattr(tariff, 'name', 'N/A'),
                tariff_mode=tariff_mode,
                mapped_strategy=mapped_strategy,
            )
            return getattr(TrafficLimitStrategy, mapped_strategy)

    # Используем глобальную настройку
    strategy = settings.DEFAULT_TRAFFIC_RESET_STRATEGY.upper()
    mapped_strategy = strategy_mapping.get(strategy, 'NO_RESET')
    logger.info('🔄 Стратегия сброса трафика из конфига', strategy=strategy, mapped_strategy=mapped_strategy)
    return getattr(TrafficLimitStrategy, mapped_strategy)


class SubscriptionService:
    def __init__(self):
        self._config_error: str | None = None
        self.api: RemnaWaveAPI | None = None
        self._last_config_signature: tuple[str, ...] | None = None

        self._refresh_configuration()

    def _refresh_configuration(self) -> None:
        auth_params = settings.get_remnawave_auth_params()
        base_url = (auth_params.get('base_url') or '').strip()
        api_key = (auth_params.get('api_key') or '').strip()
        secret_key = (auth_params.get('secret_key') or '').strip() or None
        username = (auth_params.get('username') or '').strip() or None
        password = (auth_params.get('password') or '').strip() or None
        caddy_token = (auth_params.get('caddy_token') or '').strip() or None
        auth_type = (auth_params.get('auth_type') or 'api_key').strip()

        config_signature = (
            base_url,
            api_key,
            secret_key or '',
            username or '',
            password or '',
            caddy_token or '',
            auth_type,
        )

        if config_signature == self._last_config_signature:
            return

        if not base_url:
            self._config_error = 'REMNAWAVE_API_URL не настроен'
            self.api = None
        elif not api_key:
            self._config_error = 'REMNAWAVE_API_KEY не настроен'
            self.api = None
        else:
            self._config_error = None
            self.api = RemnaWaveAPI(
                base_url=base_url,
                api_key=api_key,
                secret_key=secret_key,
                username=username,
                password=password,
                caddy_token=caddy_token,
                auth_type=auth_type,
            )

        if self._config_error:
            logger.warning(
                'RemnaWave API недоступен: . Подписочный сервис будет работать в оффлайн-режиме.',
                config_error=self._config_error,
            )

        self._last_config_signature = config_signature

    @staticmethod
    def _resolve_user_tag(subscription: Subscription) -> str | None:
        if getattr(subscription, 'is_trial', False):
            return settings.get_trial_user_tag()

        return settings.get_paid_subscription_user_tag()

    @property
    def is_configured(self) -> bool:
        return self._config_error is None

    @property
    def configuration_error(self) -> str | None:
        return self._config_error

    def _ensure_configured(self) -> None:
        self._refresh_configuration()
        if not self.api or not self.is_configured:
            raise RemnaWaveAPIError(self._config_error or 'RemnaWave API не настроен')

    @asynccontextmanager
    async def get_api_client(self):
        self._ensure_configured()
        assert self.api is not None
        async with self.api as api:
            yield api

    async def create_remnawave_user(
        self,
        db: AsyncSession,
        subscription: Subscription,
        *,
        reset_traffic: bool = False,
        reset_reason: str | None = None,
        commit: bool = True,
    ) -> RemnaWaveUser | None:
        try:
            user = await get_user_by_id(db, subscription.user_id)
            if not user:
                logger.error('Пользователь не найден', user_id=subscription.user_id)
                return None

            validation_success = await self.validate_and_clean_subscription(db, subscription, user)
            if not validation_success:
                logger.error('Ошибка валидации подписки для пользователя', _format_user_log=self._format_user_log(user))
                return None

            # Загружаем tariff заранее, чтобы избежать lazy loading в async контексте
            try:
                await db.refresh(subscription, ['tariff'])
            except Exception:
                pass  # tariff может быть None или уже загружен

            user_tag = self._resolve_user_tag(subscription)

            restore_metered_access_if_available(subscription)

            async with self.get_api_client() as api:
                hwid_limit = resolve_hwid_device_limit_for_payload(subscription)

                # Ищем существующего пользователя в панели
                existing_users = []
                if user.remnawave_uuid:
                    try:
                        existing_user = await api.get_user_by_uuid(user.remnawave_uuid)
                        if existing_user:
                            existing_users = [existing_user]
                    except Exception:
                        pass

                if not existing_users and user.telegram_id:
                    existing_users = await api.get_user_by_telegram_id(user.telegram_id)

                # Fallback: поиск по email (для OAuth юзеров без telegram_id)
                if not existing_users and user.email:
                    try:
                        existing_users = await api.get_user_by_email(user.email)
                    except Exception:
                        pass

                if existing_users:
                    logger.info(
                        '🔄 Найден существующий пользователь в панели для', _format_user_log=self._format_user_log(user)
                    )
                    remnawave_user = existing_users[0]

                    try:
                        await api.reset_user_devices(remnawave_user.uuid)
                        logger.info('🔧 Сброшены HWID устройства для', _format_user_log=self._format_user_log(user))
                    except Exception as hwid_error:
                        logger.warning('⚠️ Не удалось сбросить HWID', hwid_error=hwid_error)

                    update_kwargs = dict(
                        uuid=remnawave_user.uuid,
                        status=UserStatus.ACTIVE,
                        expire_at=subscription.end_date,
                        traffic_limit_bytes=panel_traffic_limit_bytes(subscription.traffic_limit_gb),
                        traffic_limit_strategy=get_traffic_reset_strategy(subscription.tariff),
                        email=user.email,  # Обновляем email в панели RemnaWave
                        description=settings.format_remnawave_user_description(
                            full_name=user.full_name,
                            username=user.username,
                            telegram_id=user.telegram_id,
                            email=user.email,
                            user_id=user.id,
                        ),
                    )

                    if subscription.connected_squads or is_metered_traffic_enabled():
                        update_kwargs['active_internal_squads'] = subscription.connected_squads

                    if user_tag is not None:
                        update_kwargs['tag'] = user_tag

                    if hwid_limit is not None:
                        update_kwargs['hwid_device_limit'] = hwid_limit

                    updated_user = await api.update_user(**update_kwargs)

                    if reset_traffic:
                        if is_metered_traffic_enabled():
                            reset_metered_cycle(
                                subscription,
                                panel_counter_bytes=updated_user.used_traffic_bytes,
                            )
                            updated_user = await api.update_user(
                                uuid=updated_user.uuid,
                                traffic_limit_bytes=0,
                                active_internal_squads=subscription.connected_squads or [],
                            )
                        else:
                            await self._reset_user_traffic(
                                api,
                                updated_user.uuid,
                                user,
                                reset_reason,
                            )

                else:
                    logger.info(
                        '🆕 Создаем нового пользователя в панели для', _format_user_log=self._format_user_log(user)
                    )
                    username = settings.format_remnawave_username(
                        full_name=user.full_name,
                        username=user.username,
                        telegram_id=user.telegram_id,
                        email=user.email,
                        user_id=user.id,
                    )
                    create_kwargs = dict(
                        username=username,
                        expire_at=subscription.end_date,
                        status=UserStatus.ACTIVE,
                        traffic_limit_bytes=panel_traffic_limit_bytes(subscription.traffic_limit_gb),
                        traffic_limit_strategy=get_traffic_reset_strategy(subscription.tariff),
                        telegram_id=user.telegram_id,  # Может быть None для email-пользователей
                        email=user.email,  # Email пользователя для панели RemnaWave
                        description=settings.format_remnawave_user_description(
                            full_name=user.full_name,
                            username=user.username,
                            telegram_id=user.telegram_id,
                            email=user.email,
                            user_id=user.id,
                        ),
                    )

                    if subscription.connected_squads or is_metered_traffic_enabled():
                        create_kwargs['active_internal_squads'] = subscription.connected_squads

                    if user_tag is not None:
                        create_kwargs['tag'] = user_tag

                    if hwid_limit is not None:
                        create_kwargs['hwid_device_limit'] = hwid_limit

                    updated_user = await api.create_user(**create_kwargs)

                    if reset_traffic:
                        if is_metered_traffic_enabled():
                            reset_metered_cycle(
                                subscription,
                                panel_counter_bytes=updated_user.used_traffic_bytes,
                            )
                            updated_user = await api.update_user(
                                uuid=updated_user.uuid,
                                traffic_limit_bytes=0,
                                active_internal_squads=subscription.connected_squads or [],
                            )
                        else:
                            await self._reset_user_traffic(
                                api,
                                updated_user.uuid,
                                user,
                                reset_reason,
                            )

                subscription.remnawave_short_uuid = updated_user.short_uuid
                subscription.subscription_url = updated_user.subscription_url
                subscription.subscription_crypto_link = updated_user.happ_crypto_link
                user.remnawave_uuid = updated_user.uuid

                if commit:
                    await db.commit()
                else:
                    await db.flush()

                logger.info('✅ Создан/обновлен RemnaWave пользователь для подписки', subscription_id=subscription.id)
                logger.info('🔗 Ссылка на подписку', subscription_url=updated_user.subscription_url)
                strategy_name = settings.DEFAULT_TRAFFIC_RESET_STRATEGY
                logger.info('📊 Стратегия сброса трафика', strategy_name=strategy_name)
                return updated_user

        except RemnaWaveAPIError as e:
            logger.error('Ошибка RemnaWave API', error=e)
            return None
        except Exception as e:
            logger.error('Ошибка создания RemnaWave пользователя', error=e)
            return None

    async def update_remnawave_user(
        self,
        db: AsyncSession,
        subscription: Subscription,
        *,
        reset_traffic: bool = False,
        reset_reason: str | None = None,
        commit: bool = True,
    ) -> RemnaWaveUser | None:
        try:
            user = await get_user_by_id(db, subscription.user_id)
            if not user or not user.remnawave_uuid:
                logger.error('RemnaWave UUID не найден для пользователя', user_id=subscription.user_id)
                return None

            # Загружаем tariff заранее, чтобы избежать lazy loading в async контексте
            try:
                await db.refresh(subscription, ['tariff'])
            except Exception:
                pass  # tariff может быть None или уже загружен

            current_time = datetime.now(UTC)
            # Определяем актуальный статус для отправки в RemnaWave
            # НЕ меняем статус подписки здесь - это задача scheduled job
            is_actually_active = (
                subscription.status == SubscriptionStatus.ACTIVE.value and subscription.end_date > current_time
            )

            # Логируем если статус и end_date не согласованы (для отладки)
            if subscription.status == SubscriptionStatus.ACTIVE.value and subscription.end_date <= current_time:
                logger.warning(
                    '⚠️ update_remnawave_user: подписка имеет статус ACTIVE, но end_date <= now . Отправляем в RemnaWave как DISABLED, но НЕ меняем статус в БД.',
                    subscription_id=subscription.id,
                    end_date=subscription.end_date,
                    current_time=current_time,
                )

            user_tag = self._resolve_user_tag(subscription)

            restore_metered_access_if_available(subscription)

            async with self.get_api_client() as api:
                hwid_limit = resolve_hwid_device_limit_for_payload(subscription)

                update_kwargs = dict(
                    uuid=user.remnawave_uuid,
                    status=UserStatus.ACTIVE if is_actually_active else UserStatus.DISABLED,
                    expire_at=subscription.end_date,
                    traffic_limit_bytes=panel_traffic_limit_bytes(subscription.traffic_limit_gb),
                    traffic_limit_strategy=get_traffic_reset_strategy(subscription.tariff),
                    email=user.email,  # Обновляем email в панели RemnaWave
                    description=settings.format_remnawave_user_description(
                        full_name=user.full_name,
                        username=user.username,
                        telegram_id=user.telegram_id,
                        email=user.email,
                        user_id=user.id,
                    ),
                )

                if subscription.connected_squads or is_metered_traffic_enabled():
                    update_kwargs['active_internal_squads'] = subscription.connected_squads

                if user_tag is not None:
                    update_kwargs['tag'] = user_tag

                if hwid_limit is not None:
                    update_kwargs['hwid_device_limit'] = hwid_limit

                updated_user = await api.update_user(**update_kwargs)

                if reset_traffic:
                    if is_metered_traffic_enabled():
                        reset_metered_cycle(
                            subscription,
                            panel_counter_bytes=updated_user.used_traffic_bytes,
                        )
                        updated_user = await api.update_user(
                            uuid=updated_user.uuid,
                            traffic_limit_bytes=0,
                            active_internal_squads=subscription.connected_squads or [],
                        )
                    else:
                        await self._reset_user_traffic(
                            api,
                            user.remnawave_uuid,
                            user,
                            reset_reason,
                        )

                subscription.subscription_url = updated_user.subscription_url
                subscription.subscription_crypto_link = updated_user.happ_crypto_link
                if commit:
                    await db.commit()
                else:
                    await db.flush()

                status_text = 'активным' if is_actually_active else 'отключенным'
                logger.info(
                    '✅ Обновлен RemnaWave пользователь со статусом',
                    remnawave_uuid=user.remnawave_uuid,
                    status_text=status_text,
                )
                strategy_name = settings.DEFAULT_TRAFFIC_RESET_STRATEGY
                logger.info('📊 Стратегия сброса трафика', strategy_name=strategy_name)
                return updated_user

        except RemnaWaveAPIError as e:
            logger.error('Ошибка RemnaWave API', error=e)
            return None
        except Exception as e:
            logger.error('Ошибка обновления RemnaWave пользователя', error=e)
            return None

    @staticmethod
    def _format_user_log(user) -> str:
        """Форматирует идентификатор пользователя для логов."""
        if user.telegram_id:
            return f'user {user.telegram_id}'
        if user.email:
            return f'user {user.id} ({user.email})'
        return f'user {user.id}'

    async def _reset_user_traffic(
        self,
        api: RemnaWaveAPI,
        user_uuid: str,
        user,  # User object вместо telegram_id
        reset_reason: str | None = None,
    ) -> None:
        if not user_uuid:
            return

        try:
            await api.reset_user_traffic(user_uuid)
            reason_text = f' ({reset_reason})' if reset_reason else ''
            logger.info(
                '🔄 Сброшен трафик RemnaWave для', _format_user_log=self._format_user_log(user), reason_text=reason_text
            )
        except Exception as exc:
            logger.warning(
                '⚠️ Не удалось сбросить трафик RemnaWave для', _format_user_log=self._format_user_log(user), error=exc
            )

    async def disable_remnawave_user(self, user_uuid: str) -> bool:
        try:
            async with self.get_api_client() as api:
                await api.disable_user(user_uuid)
                logger.info('✅ Отключен RemnaWave пользователь', user_uuid=user_uuid)
                return True

        except Exception as e:
            error_msg = str(e).lower()
            # "User already disabled" - считаем успехом
            if 'already disabled' in error_msg:
                logger.info('✅ RemnaWave пользователь уже отключен', user_uuid=user_uuid)
                return True
            logger.error('Ошибка отключения RemnaWave пользователя', error=e)
            return False

    async def enable_remnawave_user(self, user_uuid: str) -> bool:
        """Включить пользователя в RemnaWave (реактивация)."""
        try:
            async with self.get_api_client() as api:
                await api.enable_user(user_uuid)
                logger.info('✅ Включен RemnaWave пользователь', user_uuid=user_uuid)
                return True

        except Exception as e:
            error_msg = str(e).lower()
            # "User already enabled" - считаем успехом
            if 'already enabled' in error_msg:
                logger.info('✅ RemnaWave пользователь уже включен', user_uuid=user_uuid)
                return True
            logger.error('Ошибка включения RemnaWave пользователя', error=e)
            return False

    async def get_remnawave_squads(self) -> list[dict] | None:
        """Получить список internal squads из RemnaWave."""
        try:
            async with self.get_api_client() as api:
                squads = await api.get_internal_squads()
                # Преобразуем в формат для sync_with_remnawave
                result = []
                for squad in squads:
                    result.append(
                        {
                            'uuid': squad.uuid,
                            'name': squad.name,
                        }
                    )
                logger.info('✅ Получено серверов из RemnaWave', result_count=len(result))
                return result

        except Exception as e:
            logger.error('Ошибка получения серверов из RemnaWave', error=e)
            return None

    async def revoke_subscription(self, db: AsyncSession, subscription: Subscription) -> str | None:
        try:
            user = await get_user_by_id(db, subscription.user_id)
            if not user or not user.remnawave_uuid:
                return None

            async with self.get_api_client() as api:
                updated_user = await api.revoke_user_subscription(user.remnawave_uuid)

                subscription.remnawave_short_uuid = updated_user.short_uuid
                subscription.subscription_url = updated_user.subscription_url
                subscription.subscription_crypto_link = updated_user.happ_crypto_link
                await db.commit()

                logger.info('✅ Обновлена ссылка подписки для', _format_user_log=self._format_user_log(user))
                return updated_user.subscription_url

        except Exception as e:
            logger.error('Ошибка обновления ссылки подписки', error=e)
            return None

    async def get_subscription_info(self, short_uuid: str) -> dict | None:
        try:
            async with self.get_api_client() as api:
                info = await api.get_subscription_info(short_uuid)
                return info

        except Exception as e:
            logger.error('Ошибка получения информации о подписке', error=e)
            return None

    async def sync_subscription_usage(self, db: AsyncSession, subscription: Subscription) -> bool:
        try:
            user = await get_user_by_id(db, subscription.user_id)
            if not user or not user.remnawave_uuid:
                return False

            async with self.get_api_client() as api:
                remnawave_user = await api.get_user_by_uuid(user.remnawave_uuid)
                if not remnawave_user:
                    return False

                if is_metered_traffic_enabled():
                    used_gb = subscription.traffic_used_gb or 0.0
                else:
                    used_gb = self._bytes_to_gb(remnawave_user.used_traffic_bytes)
                    subscription.traffic_used_gb = used_gb

                await db.commit()

                logger.debug('Синхронизирован трафик для подписки ГБ', subscription_id=subscription.id, used_gb=used_gb)
                return True

        except Exception as e:
            logger.error('Ошибка синхронизации трафика', error=e)
            return False

    async def ensure_subscription_synced(
        self,
        db: AsyncSession,
        subscription: Subscription,
    ) -> tuple[bool, str | None]:
        """
        Проверяет и синхронизирует подписку с RemnaWave при необходимости.

        Если subscription_url отсутствует или данные не синхронизированы,
        пытается обновить/создать пользователя в RemnaWave.

        Returns:
            Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            user = await get_user_by_id(db, subscription.user_id)
            if not user:
                logger.error('Пользователь не найден для подписки', subscription_id=subscription.id)
                return False, 'user_not_found'

            # Проверяем, нужна ли синхронизация
            needs_sync = not subscription.subscription_url or not user.remnawave_uuid

            if not needs_sync:
                # Проверяем, существует ли пользователь в RemnaWave
                try:
                    async with self.get_api_client() as api:
                        remnawave_user = await api.get_user_by_uuid(user.remnawave_uuid)
                        if not remnawave_user:
                            needs_sync = True
                            logger.warning(
                                'Пользователь не найден в RemnaWave, требуется синхронизация',
                                remnawave_uuid=user.remnawave_uuid,
                            )
                except Exception as check_error:
                    logger.warning('Не удалось проверить пользователя в RemnaWave', check_error=check_error)
                    # Продолжаем, возможно проблема временная

            if not needs_sync:
                return True, None

            logger.info(
                'Синхронизация подписки с RemnaWave (subscription_url=, remnawave_uuid=)',
                subscription_id=subscription.id,
                subscription_url=bool(subscription.subscription_url),
                remnawave_uuid=bool(user.remnawave_uuid),
            )

            # Пытаемся синхронизировать
            result = None
            if user.remnawave_uuid:
                # Пробуем обновить существующего пользователя
                result = await self.update_remnawave_user(
                    db,
                    subscription,
                    reset_traffic=False,
                )
                # Если update не удался (пользователь удалён из RemnaWave) — пробуем создать
                if not result:
                    logger.warning(
                        'Не удалось обновить пользователя в RemnaWave, пробуем создать заново',
                        remnawave_uuid=user.remnawave_uuid,
                    )
                    # Сбрасываем старый UUID, create_remnawave_user установит новый
                    user.remnawave_uuid = None
                    result = await self.create_remnawave_user(
                        db,
                        subscription,
                        reset_traffic=False,
                    )
            else:
                # Создаём нового пользователя
                result = await self.create_remnawave_user(
                    db,
                    subscription,
                    reset_traffic=False,
                )

            if result:
                await db.refresh(subscription)
                await db.refresh(user)
                logger.info(
                    'Подписка успешно синхронизирована с RemnaWave. URL',
                    subscription_id=subscription.id,
                    subscription_url=subscription.subscription_url,
                )
                return True, None
            logger.error('Не удалось синхронизировать подписку с RemnaWave', subscription_id=subscription.id)
            return False, 'sync_failed'

        except RemnaWaveAPIError as api_error:
            logger.error(
                'Ошибка RemnaWave API при синхронизации подписки', subscription_id=subscription.id, api_error=api_error
            )
            return False, 'api_error'
        except Exception as e:
            logger.error('Ошибка синхронизации подписки', subscription_id=subscription.id, error=e)
            return False, 'unknown_error'

    async def calculate_subscription_price(
        self,
        period_days: int,
        traffic_gb: int,
        server_squad_ids: list[int],
        devices: int,
        db: AsyncSession,
        *,
        user: User | None = None,
        promo_group: PromoGroup | None = None,
    ) -> tuple[int, list[int]]:
        from app.config import PERIOD_PRICES
        from app.database.crud.server_squad import get_server_squad_by_id

        if settings.MAX_DEVICES_LIMIT > 0 and devices > settings.MAX_DEVICES_LIMIT:
            raise ValueError(f'Превышен максимальный лимит устройств: {settings.MAX_DEVICES_LIMIT}')

        base_price_original = PERIOD_PRICES.get(period_days, 0)
        period_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'period',
            period_days=period_days,
        )
        base_discount_total = base_price_original * period_discount_percent // 100
        base_price = base_price_original - base_discount_total

        promo_group = promo_group or (user.get_primary_promo_group() if user else None)

        traffic_price = settings.get_traffic_price(traffic_gb)
        traffic_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'traffic',
            period_days=period_days,
        )
        traffic_discount = traffic_price * traffic_discount_percent // 100
        discounted_traffic_price = traffic_price - traffic_discount

        server_prices = []
        total_servers_price = 0
        servers_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'servers',
            period_days=period_days,
        )

        for server_id in server_squad_ids:
            server = await get_server_squad_by_id(db, server_id)
            if server and server.is_available and not server.is_full:
                server_price = server.price_kopeks
                server_discount = server_price * servers_discount_percent // 100
                discounted_server_price = server_price - server_discount
                server_prices.append(discounted_server_price)
                total_servers_price += discounted_server_price
                log_message = f'Сервер {server.display_name}: {server_price / 100}₽'
                if server_discount > 0:
                    log_message += f' (скидка {servers_discount_percent}%: -{server_discount / 100}₽ → {discounted_server_price / 100}₽)'
                logger.debug(log_message)
            else:
                server_prices.append(0)
                logger.warning('Сервер ID недоступен', server_id=server_id)

        devices_price = max(0, devices - settings.DEFAULT_DEVICE_LIMIT) * settings.PRICE_PER_DEVICE
        devices_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'devices',
            period_days=period_days,
        )
        devices_discount = devices_price * devices_discount_percent // 100
        discounted_devices_price = devices_price - devices_discount

        total_price = base_price + discounted_traffic_price + total_servers_price + discounted_devices_price

        logger.debug('Расчет стоимости новой подписки:')
        base_log = f'   Период {period_days} дней: {base_price_original / 100}₽'
        if base_discount_total > 0:
            base_log += f' → {base_price / 100}₽ (скидка {period_discount_percent}%: -{base_discount_total / 100}₽)'
        logger.debug(base_log)
        if discounted_traffic_price > 0:
            message = f'   Трафик {traffic_gb} ГБ: {traffic_price / 100}₽'
            if traffic_discount > 0:
                message += f' (скидка {traffic_discount_percent}%: -{traffic_discount / 100}₽ → {discounted_traffic_price / 100}₽)'
            logger.debug(message)
        if total_servers_price > 0:
            message = f'   Серверы ({len(server_squad_ids)}): {total_servers_price / 100}₽'
            if servers_discount_percent > 0:
                message += f' (скидка {servers_discount_percent}% применяется ко всем серверам)'
            logger.debug(message)
        if discounted_devices_price > 0:
            message = f'   Устройства ({devices}): {devices_price / 100}₽'
            if devices_discount > 0:
                message += f' (скидка {devices_discount_percent}%: -{devices_discount / 100}₽ → {discounted_devices_price / 100}₽)'
            logger.debug(message)
        logger.debug('ИТОГО: ₽', total_price=total_price / 100)

        return total_price, server_prices

    async def calculate_renewal_price(
        self,
        subscription: Subscription,
        period_days: int,
        db: AsyncSession,
        *,
        user: User | None = None,
        promo_group: PromoGroup | None = None,
    ) -> int:
        try:
            from app.config import PERIOD_PRICES

            # Use subscription's tariff price if available, fall back to global PERIOD_PRICES
            tariff = getattr(subscription, 'tariff', None)
            tariff_price = tariff.get_price_for_period(period_days) if tariff else None
            base_price_original = tariff_price if tariff_price is not None else PERIOD_PRICES.get(period_days, 0)

            if user is None:
                user = getattr(subscription, 'user', None)
            promo_group = promo_group or (user.get_primary_promo_group() if user else None)

            servers_price, _ = await self.get_countries_price_by_uuids(
                subscription.connected_squads,
                db,
                promo_group_id=promo_group.id if promo_group else None,
            )

            servers_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'servers',
                period_days=period_days,
            )
            servers_discount = servers_price * servers_discount_percent // 100
            discounted_servers_price = servers_price - servers_discount

            device_limit = subscription.device_limit
            if device_limit is None:
                if settings.is_devices_selection_enabled():
                    device_limit = settings.DEFAULT_DEVICE_LIMIT
                else:
                    forced_limit = settings.get_disabled_mode_device_limit()
                    if forced_limit is None:
                        device_limit = settings.DEFAULT_DEVICE_LIMIT
                    else:
                        device_limit = forced_limit

            devices_price = max(0, (device_limit or 0) - settings.DEFAULT_DEVICE_LIMIT) * settings.PRICE_PER_DEVICE
            devices_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'devices',
                period_days=period_days,
            )
            devices_discount = devices_price * devices_discount_percent // 100
            discounted_devices_price = devices_price - devices_discount

            # В режиме fixed_with_topup при продлении используем фиксированный лимит
            if settings.is_traffic_fixed():
                renewal_traffic_gb = settings.get_fixed_traffic_limit()
            else:
                renewal_traffic_gb = subscription.traffic_limit_gb
            traffic_price = settings.get_traffic_price(renewal_traffic_gb)
            traffic_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'traffic',
                period_days=period_days,
            )
            traffic_discount = traffic_price * traffic_discount_percent // 100
            discounted_traffic_price = traffic_price - traffic_discount

            period_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'period',
                period_days=period_days,
            )
            base_discount_total = base_price_original * period_discount_percent // 100
            base_price = base_price_original - base_discount_total

            total_price = base_price + discounted_servers_price + discounted_devices_price + discounted_traffic_price

            logger.debug(
                '💰 Расчет стоимости продления для подписки (по текущим ценам)', subscription_id=subscription.id
            )
            base_log = f'   📅 Период {period_days} дней: {base_price_original / 100}₽'
            if base_discount_total > 0:
                base_log += f' → {base_price / 100}₽ (скидка {period_discount_percent}%: -{base_discount_total / 100}₽)'
            logger.debug(base_log)
            if servers_price > 0:
                message = f'   🌍 Серверы ({len(subscription.connected_squads)}) по текущим ценам: {discounted_servers_price / 100}₽'
                if servers_discount > 0:
                    message += (
                        f' (скидка {servers_discount_percent}%: -{servers_discount / 100}₽ от {servers_price / 100}₽)'
                    )
                logger.debug(message)
            if devices_price > 0:
                message = f'   📱 Устройства ({device_limit}): {discounted_devices_price / 100}₽'
                if devices_discount > 0:
                    message += (
                        f' (скидка {devices_discount_percent}%: -{devices_discount / 100}₽ от {devices_price / 100}₽)'
                    )
                logger.debug(message)
            if traffic_price > 0:
                message = f'   📊 Трафик ({subscription.traffic_limit_gb} ГБ): {discounted_traffic_price / 100}₽'
                if traffic_discount > 0:
                    message += (
                        f' (скидка {traffic_discount_percent}%: -{traffic_discount / 100}₽ от {traffic_price / 100}₽)'
                    )
                logger.debug(message)
            logger.debug('💎 ИТОГО: ₽', total_price=total_price / 100)

            return total_price

        except Exception as e:
            logger.error('Ошибка расчета стоимости продления', error=e)
            from app.config import PERIOD_PRICES

            return PERIOD_PRICES.get(period_days, 0)

    async def validate_and_clean_subscription(self, db: AsyncSession, subscription: Subscription, user: User) -> bool:
        try:
            needs_cleanup = False
            user_log = self._format_user_log(user)

            if user.remnawave_uuid:
                try:
                    async with self.get_api_client() as api:
                        remnawave_user = await api.get_user_by_uuid(user.remnawave_uuid)

                        if not remnawave_user:
                            logger.warning(
                                '⚠️ Пользователь имеет UUID но не найден в панели',
                                user_log=user_log,
                                remnawave_uuid=user.remnawave_uuid,
                            )
                            needs_cleanup = True
                        # Проверяем telegram_id только если он задан у обоих
                        elif (
                            user.telegram_id
                            and remnawave_user.telegram_id
                            and remnawave_user.telegram_id != user.telegram_id
                        ):
                            logger.warning(
                                '⚠️ Несоответствие telegram_id для panel',
                                user_log=user_log,
                                telegram_id=remnawave_user.telegram_id,
                            )
                            needs_cleanup = True
                except Exception as api_error:
                    logger.error('❌ Ошибка проверки пользователя в панели', api_error=api_error)
                    needs_cleanup = True

            if subscription.remnawave_short_uuid and not user.remnawave_uuid:
                logger.warning('⚠️ У подписки есть short_uuid, но у пользователя нет remnawave_uuid')
                needs_cleanup = True

            if needs_cleanup:
                logger.info('🧹 Очищаем мусорные данные подписки для', user_log=user_log)

                subscription.remnawave_short_uuid = None
                subscription.subscription_url = ''
                subscription.subscription_crypto_link = ''
                subscription.connected_squads = []

                user.remnawave_uuid = None

                await db.commit()
                logger.info('✅ Мусорные данные очищены для', user_log=user_log)

            return True

        except Exception as e:
            logger.error('❌ Ошибка валидации подписки для', _format_user_log=self._format_user_log(user), error=e)
            await db.rollback()
            return False

    async def get_countries_price_by_uuids(
        self,
        country_uuids: list[str],
        db: AsyncSession,
        *,
        promo_group_id: int | None = None,
    ) -> tuple[int, list[int]]:
        try:
            from app.database.crud.server_squad import get_server_squad_by_uuid

            total_price = 0
            prices_list = []

            for country_uuid in country_uuids:
                server = await get_server_squad_by_uuid(db, country_uuid)
                is_allowed = True
                if promo_group_id is not None and server:
                    allowed_ids = {pg.id for pg in server.allowed_promo_groups}
                    is_allowed = promo_group_id in allowed_ids

                if server and server.is_available and not server.is_full and is_allowed:
                    price = server.price_kopeks
                    total_price += price
                    prices_list.append(price)
                    logger.debug('🏷️ Страна ₽', display_name=server.display_name, price=price / 100)
                else:
                    default_price = 0
                    total_price += default_price
                    prices_list.append(default_price)
                    logger.warning(
                        '⚠️ Сервер недоступен, используем базовую цену: ₽',
                        country_uuid=country_uuid,
                        default_price=default_price / 100,
                    )

            logger.info('💰 Общая стоимость стран: ₽', total_price=total_price / 100)
            return total_price, prices_list

        except Exception as e:
            logger.error('Ошибка получения цен стран', error=e)
            default_prices = [0] * len(country_uuids)
            return sum(default_prices), default_prices

    async def _get_countries_price(self, country_uuids: list[str], db: AsyncSession) -> int:
        try:
            total_price, _ = await self.get_countries_price_by_uuids(country_uuids, db)
            return total_price
        except Exception as e:
            logger.error('Ошибка получения цен стран', error=e)
            return len(country_uuids) * 1000

    async def calculate_subscription_price_with_months(
        self,
        period_days: int,
        traffic_gb: int,
        server_squad_ids: list[int],
        devices: int,
        db: AsyncSession,
        *,
        user: User | None = None,
        promo_group: PromoGroup | None = None,
    ) -> tuple[int, list[int]]:
        from app.config import PERIOD_PRICES
        from app.database.crud.server_squad import get_server_squad_by_id

        if settings.MAX_DEVICES_LIMIT > 0 and devices > settings.MAX_DEVICES_LIMIT:
            raise ValueError(f'Превышен максимальный лимит устройств: {settings.MAX_DEVICES_LIMIT}')

        months_in_period = calculate_months_from_days(period_days)

        base_price_original = PERIOD_PRICES.get(period_days, 0)
        period_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'period',
            period_days=period_days,
        )
        base_discount_total = base_price_original * period_discount_percent // 100
        base_price = base_price_original - base_discount_total

        promo_group = promo_group or (user.get_primary_promo_group() if user else None)

        traffic_price_per_month = settings.get_traffic_price(traffic_gb)
        traffic_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'traffic',
            period_days=period_days,
        )
        traffic_discount_per_month = traffic_price_per_month * traffic_discount_percent // 100
        discounted_traffic_per_month = traffic_price_per_month - traffic_discount_per_month
        total_traffic_price = discounted_traffic_per_month * months_in_period

        server_prices = []
        total_servers_price = 0
        servers_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'servers',
            period_days=period_days,
        )

        for server_id in server_squad_ids:
            server = await get_server_squad_by_id(db, server_id)
            if server and server.is_available and not server.is_full:
                server_price_per_month = server.price_kopeks
                server_discount_per_month = server_price_per_month * servers_discount_percent // 100
                discounted_server_per_month = server_price_per_month - server_discount_per_month
                server_price_total = discounted_server_per_month * months_in_period
                server_prices.append(server_price_total)
                total_servers_price += server_price_total
                log_message = f'Сервер {server.display_name}: {server_price_per_month / 100}₽/мес x {months_in_period} мес = {server_price_total / 100}₽'
                if server_discount_per_month > 0:
                    log_message += (
                        f' (скидка {servers_discount_percent}%: -{server_discount_per_month * months_in_period / 100}₽)'
                    )
                logger.debug(log_message)
            else:
                server_prices.append(0)
                logger.warning('Сервер ID недоступен', server_id=server_id)

        additional_devices = max(0, devices - settings.DEFAULT_DEVICE_LIMIT)
        devices_price_per_month = additional_devices * settings.PRICE_PER_DEVICE
        devices_discount_percent = _resolve_discount_percent(
            user,
            promo_group,
            'devices',
            period_days=period_days,
        )
        devices_discount_per_month = devices_price_per_month * devices_discount_percent // 100
        discounted_devices_per_month = devices_price_per_month - devices_discount_per_month
        total_devices_price = discounted_devices_per_month * months_in_period

        total_price = base_price + total_traffic_price + total_servers_price + total_devices_price

        logger.debug(
            'Расчет стоимости новой подписки на дней ( мес)', period_days=period_days, months_in_period=months_in_period
        )
        base_log = f'   Период {period_days} дней: {base_price_original / 100}₽'
        if base_discount_total > 0:
            base_log += f' → {base_price / 100}₽ (скидка {period_discount_percent}%: -{base_discount_total / 100}₽)'
        logger.debug(base_log)
        if total_traffic_price > 0:
            message = f'   Трафик {traffic_gb} ГБ: {traffic_price_per_month / 100}₽/мес x {months_in_period} = {total_traffic_price / 100}₽'
            if traffic_discount_per_month > 0:
                message += (
                    f' (скидка {traffic_discount_percent}%: -{traffic_discount_per_month * months_in_period / 100}₽)'
                )
            logger.debug(message)
        if total_servers_price > 0:
            message = f'   Серверы ({len(server_squad_ids)}): {total_servers_price / 100}₽'
            if servers_discount_percent > 0:
                message += f' (скидка {servers_discount_percent}% применяется ко всем серверам)'
            logger.debug(message)
        if total_devices_price > 0:
            message = f'   Устройства ({additional_devices}): {devices_price_per_month / 100}₽/мес x {months_in_period} = {total_devices_price / 100}₽'
            if devices_discount_per_month > 0:
                message += (
                    f' (скидка {devices_discount_percent}%: -{devices_discount_per_month * months_in_period / 100}₽)'
                )
            logger.debug(message)
        logger.debug('ИТОГО: ₽', total_price=total_price / 100)

        return total_price, server_prices

    async def calculate_renewal_price_with_months(
        self,
        subscription: Subscription,
        period_days: int,
        db: AsyncSession,
        *,
        user: User | None = None,
        promo_group: PromoGroup | None = None,
    ) -> int:
        try:
            from app.config import PERIOD_PRICES

            months_in_period = calculate_months_from_days(period_days)

            # Use subscription's tariff price if available, fall back to global PERIOD_PRICES
            tariff = getattr(subscription, 'tariff', None)
            tariff_price = tariff.get_price_for_period(period_days) if tariff else None
            base_price_original = tariff_price if tariff_price is not None else PERIOD_PRICES.get(period_days, 0)

            if user is None:
                user = getattr(subscription, 'user', None)
            promo_group = promo_group or (user.get_primary_promo_group() if user else None)

            servers_price_per_month, _ = await self.get_countries_price_by_uuids(
                subscription.connected_squads,
                db,
                promo_group_id=promo_group.id if promo_group else None,
            )
            servers_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'servers',
                period_days=period_days,
            )
            servers_discount_per_month = servers_price_per_month * servers_discount_percent // 100
            discounted_servers_per_month = servers_price_per_month - servers_discount_per_month
            total_servers_price = discounted_servers_per_month * months_in_period

            device_limit = subscription.device_limit
            if device_limit is None:
                if settings.is_devices_selection_enabled():
                    device_limit = settings.DEFAULT_DEVICE_LIMIT
                else:
                    forced_limit = settings.get_disabled_mode_device_limit()
                    if forced_limit is None:
                        device_limit = settings.DEFAULT_DEVICE_LIMIT
                    else:
                        device_limit = forced_limit

            additional_devices = max(0, (device_limit or 0) - settings.DEFAULT_DEVICE_LIMIT)
            devices_price_per_month = additional_devices * settings.PRICE_PER_DEVICE
            devices_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'devices',
                period_days=period_days,
            )
            devices_discount_per_month = devices_price_per_month * devices_discount_percent // 100
            discounted_devices_per_month = devices_price_per_month - devices_discount_per_month
            total_devices_price = discounted_devices_per_month * months_in_period

            # В режиме fixed_with_topup при продлении используем фиксированный лимит
            if settings.is_traffic_fixed():
                renewal_traffic_gb = settings.get_fixed_traffic_limit()
            else:
                renewal_traffic_gb = subscription.traffic_limit_gb
            traffic_price_per_month = settings.get_traffic_price(renewal_traffic_gb)
            traffic_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'traffic',
                period_days=period_days,
            )
            traffic_discount_per_month = traffic_price_per_month * traffic_discount_percent // 100
            discounted_traffic_per_month = traffic_price_per_month - traffic_discount_per_month
            total_traffic_price = discounted_traffic_per_month * months_in_period

            period_discount_percent = _resolve_discount_percent(
                user,
                promo_group,
                'period',
                period_days=period_days,
            )
            base_discount_total = base_price_original * period_discount_percent // 100
            base_price = base_price_original - base_discount_total

            total_price = base_price + total_servers_price + total_devices_price + total_traffic_price

            logger.debug(
                '💰 Расчет стоимости продления подписки на дней ( мес)',
                subscription_id=subscription.id,
                period_days=period_days,
                months_in_period=months_in_period,
            )
            base_log = f'   📅 Период {period_days} дней: {base_price_original / 100}₽'
            if base_discount_total > 0:
                base_log += f' → {base_price / 100}₽ (скидка {period_discount_percent}%: -{base_discount_total / 100}₽)'
            logger.debug(base_log)
            if total_servers_price > 0:
                message = f'   🌍 Серверы: {servers_price_per_month / 100}₽/мес x {months_in_period} = {total_servers_price / 100}₽'
                if servers_discount_per_month > 0:
                    message += f' (скидка {servers_discount_percent}%: -{servers_discount_per_month * months_in_period / 100}₽)'
                logger.debug(message)
            if total_devices_price > 0:
                message = f'   📱 Устройства: {devices_price_per_month / 100}₽/мес x {months_in_period} = {total_devices_price / 100}₽'
                if devices_discount_per_month > 0:
                    message += f' (скидка {devices_discount_percent}%: -{devices_discount_per_month * months_in_period / 100}₽)'
                logger.debug(message)
            if total_traffic_price > 0:
                message = f'   📊 Трафик: {traffic_price_per_month / 100}₽/мес x {months_in_period} = {total_traffic_price / 100}₽'
                if traffic_discount_per_month > 0:
                    message += f' (скидка {traffic_discount_percent}%: -{traffic_discount_per_month * months_in_period / 100}₽)'
                logger.debug(message)
            logger.debug('💎 ИТОГО: ₽', total_price=total_price / 100)

            return total_price

        except Exception as e:
            logger.error('Ошибка расчета стоимости продления', error=e)
            from app.config import PERIOD_PRICES

            return PERIOD_PRICES.get(period_days, 0)

    async def calculate_addon_price_with_remaining_period(
        self,
        subscription: Subscription,
        additional_traffic_gb: int = 0,
        additional_devices: int = 0,
        additional_server_ids: list[int] = None,
        db: AsyncSession = None,
    ) -> int:
        if additional_server_ids is None:
            additional_server_ids = []

        months_to_pay = get_remaining_months(subscription.end_date)
        period_hint_days = months_to_pay * 30 if months_to_pay > 0 else None

        user = getattr(subscription, 'user', None)
        promo_group = user.promo_group if user else None

        total_price = 0

        if additional_traffic_gb > 0:
            traffic_price_per_month = settings.get_traffic_price(additional_traffic_gb)
            traffic_discount_percent = _resolve_addon_discount_percent(
                user,
                promo_group,
                'traffic',
                period_days=period_hint_days,
            )
            traffic_discount_per_month = traffic_price_per_month * traffic_discount_percent // 100
            discounted_traffic_per_month = traffic_price_per_month - traffic_discount_per_month
            traffic_total_price = discounted_traffic_per_month * months_to_pay
            total_price += traffic_total_price
            message = (
                f'Трафик +{additional_traffic_gb}ГБ: {traffic_price_per_month / 100}₽/мес x {months_to_pay}'
                f' = {traffic_total_price / 100}₽'
            )
            if traffic_discount_per_month > 0:
                message += (
                    f' (скидка {traffic_discount_percent}%: -{traffic_discount_per_month * months_to_pay / 100}₽)'
                )
            logger.info(message)

        if additional_devices > 0:
            devices_price_per_month = additional_devices * settings.PRICE_PER_DEVICE
            devices_discount_percent = _resolve_addon_discount_percent(
                user,
                promo_group,
                'devices',
                period_days=period_hint_days,
            )
            devices_discount_per_month = devices_price_per_month * devices_discount_percent // 100
            discounted_devices_per_month = devices_price_per_month - devices_discount_per_month
            devices_total_price = discounted_devices_per_month * months_to_pay
            total_price += devices_total_price
            message = (
                f'Устройства +{additional_devices}: {devices_price_per_month / 100}₽/мес x {months_to_pay}'
                f' = {devices_total_price / 100}₽'
            )
            if devices_discount_per_month > 0:
                message += (
                    f' (скидка {devices_discount_percent}%: -{devices_discount_per_month * months_to_pay / 100}₽)'
                )
            logger.info(message)

        if additional_server_ids and db:
            for server_id in additional_server_ids:
                from app.database.crud.server_squad import get_server_squad_by_id

                server = await get_server_squad_by_id(db, server_id)
                if server and server.is_available:
                    server_price_per_month = server.price_kopeks
                    servers_discount_percent = _resolve_addon_discount_percent(
                        user,
                        promo_group,
                        'servers',
                        period_days=period_hint_days,
                    )
                    server_discount_per_month = server_price_per_month * servers_discount_percent // 100
                    discounted_server_per_month = server_price_per_month - server_discount_per_month
                    server_total_price = discounted_server_per_month * months_to_pay
                    total_price += server_total_price
                    message = (
                        f'Сервер {server.display_name}: {server_price_per_month / 100}₽/мес x {months_to_pay}'
                        f' = {server_total_price / 100}₽'
                    )
                    if server_discount_per_month > 0:
                        message += (
                            f' (скидка {servers_discount_percent}%:'
                            f' -{server_discount_per_month * months_to_pay / 100}₽)'
                        )
                    logger.info(message)

        logger.info('Итого доплата за мес: ₽', months_to_pay=months_to_pay, total_price=total_price / 100)
        return total_price

    def _gb_to_bytes(self, gb: int | None) -> int:
        if not gb:  # None or 0
            return 0
        return gb * 1024 * 1024 * 1024

    def _bytes_to_gb(self, bytes_value: int) -> float:
        if bytes_value == 0:
            return 0.0
        return bytes_value / (1024 * 1024 * 1024)
