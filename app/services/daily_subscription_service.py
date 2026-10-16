"""
Сервис для автоматического списания суточных подписок.
Проверяет подписки с суточным тарифом и списывает плату раз в сутки.
Также сбрасывает докупленный трафик по истечении 30 дней.
"""

import asyncio
from datetime import UTC, datetime

import structlog
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.advisory_lock import distributed_job_lock
from app.database.crud.subscription import (
    get_daily_subscriptions_for_charge,
    suspend_daily_subscription_insufficient_balance,
    update_daily_charge_time,
)
from app.database.crud.transaction import create_transaction, emit_transaction_side_effects
from app.database.crud.user import get_user_by_id, subtract_user_balance
from app.database.database import AsyncSessionLocal
from app.database.models import PaymentMethod, Subscription, TransactionType, User
from app.localization.texts import get_texts
from app.services.notification_delivery_service import (
    NotificationType,
    notification_delivery_service,
)
from app.services.traffic_purchase_service import remove_expired_traffic_purchases


logger = structlog.get_logger(__name__)

_DAILY_CHARGES_LOCK_ID = 7_612_946_175_504_209_052
_TRAFFIC_EXPIRY_LOCK_ID = 7_612_946_175_504_209_053


class DailySubscriptionService:
    """
    Сервис автоматического списания для суточных подписок.
    """

    def __init__(self):
        self._running = False
        self._bot: Bot | None = None
        self._check_interval_minutes = 30  # Проверка каждые 30 минут

    def set_bot(self, bot: Bot):
        """Устанавливает бота для отправки уведомлений."""
        self._bot = bot

    def is_daily_charges_enabled(self) -> bool:
        """Return True when daily tariff auto-charging is enabled."""
        return getattr(settings, 'DAILY_SUBSCRIPTIONS_ENABLED', True)

    def is_traffic_resets_enabled(self) -> bool:
        """Return True when purchased traffic expiry processing is enabled."""
        return getattr(settings, 'TRAFFIC_TOPUP_EXPIRY_ENABLED', True)

    def is_enabled(self) -> bool:
        """Проверяет, включен ли сервис суточных подписок."""
        return self.is_daily_charges_enabled() or self.is_traffic_resets_enabled()

    def get_check_interval_minutes(self) -> int:
        """Возвращает интервал проверки в минутах."""
        return getattr(settings, 'DAILY_SUBSCRIPTIONS_CHECK_INTERVAL_MINUTES', 30)

    def get_traffic_reset_check_interval_seconds(self) -> int:
        """Return traffic top-up expiry check interval."""
        return max(10, int(getattr(settings, 'TRAFFIC_TOPUP_EXPIRY_CHECK_INTERVAL_SECONDS', 60) or 60))

    async def process_daily_charges(self) -> dict:
        """
        Обрабатывает суточные списания.

        Returns:
            dict: Статистика обработки
        """
        stats = {
            'checked': 0,
            'charged': 0,
            'suspended': 0,
            'errors': 0,
        }

        try:
            async with distributed_job_lock(_DAILY_CHARGES_LOCK_ID, name='daily-subscription-charges') as acquired:
                if not acquired:
                    return stats

                async with AsyncSessionLocal() as db:
                    try:
                        subscriptions = await get_daily_subscriptions_for_charge(db)
                        stats['checked'] = len(subscriptions)

                        for subscription in subscriptions:
                            try:
                                result = await self._process_single_charge(db, subscription)
                                if result == 'charged':
                                    stats['charged'] += 1
                                elif result == 'suspended':
                                    stats['suspended'] += 1
                                elif result == 'error':
                                    stats['errors'] += 1
                                    break
                            except Exception as e:
                                await db.rollback()
                                logger.error(
                                    'Ошибка обработки суточной подписки',
                                    subscription_id=subscription.id,
                                    error=e,
                                    exc_info=True,
                                )
                                stats['errors'] += 1
                                break
                    except Exception as e:
                        logger.error('Ошибка при обработке подписок', error=e, exc_info=True)
                        await db.rollback()

        except Exception as e:
            logger.error('Ошибка при получении подписок для списания', error=e, exc_info=True)

        return stats

    async def _process_single_charge(self, db, subscription) -> str:
        """
        Обрабатывает списание для одной подписки.

        Returns:
            str: "charged", "suspended", "error", "skipped"
        """
        user = subscription.user
        if not user:
            user = await get_user_by_id(db, subscription.user_id)

        if not user:
            logger.warning('Пользователь не найден для подписки', subscription_id=subscription.id)
            return 'error'

        tariff = subscription.tariff
        if not tariff:
            logger.warning('Тариф не найден для подписки', subscription_id=subscription.id)
            return 'error'

        daily_price = tariff.daily_price_kopeks
        if daily_price <= 0:
            logger.warning('Некорректная суточная цена для тарифа', tariff_id=tariff.id)
            return 'error'

        # Проверяем баланс
        if user.balance_kopeks < daily_price:
            # Недостаточно средств - приостанавливаем подписку
            await suspend_daily_subscription_insufficient_balance(db, subscription, commit=False)
            await db.commit()

            # Уведомляем пользователя
            if self._bot:
                await self._notify_insufficient_balance(user, subscription, daily_price)

            logger.info(
                'Подписка приостановлена: недостаточно средств (баланс: требуется: )',
                subscription_id=subscription.id,
                balance_kopeks=user.balance_kopeks,
                daily_price=daily_price,
            )
            return 'suspended'

        # Списываем средства
        description = f'Суточная оплата тарифа «{tariff.name}»'

        try:
            deducted = await subtract_user_balance(
                db,
                user,
                daily_price,
                description,
                mark_as_paid_subscription=True,
                commit=False,
            )

            if not deducted:
                logger.warning('Не удалось списать средства для подписки', subscription_id=subscription.id)
                return 'error'

            # Создаём транзакцию
            transaction = await create_transaction(
                db=db,
                user_id=user.id,
                type=TransactionType.SUBSCRIPTION_PAYMENT,
                amount_kopeks=daily_price,
                description=description,
                payment_method=PaymentMethod.BALANCE,
                commit=False,
            )

            # Обновляем время последнего списания и продлеваем подписку
            old_end_date = subscription.end_date
            subscription = await update_daily_charge_time(db, subscription, commit=False)
            await db.commit()
            await emit_transaction_side_effects(
                db,
                transaction,
                amount_kopeks=daily_price,
                user_id=user.id,
                type=TransactionType.SUBSCRIPTION_PAYMENT,
                payment_method=PaymentMethod.BALANCE,
                description=description,
            )

            user_id_display = user.telegram_id or user.email or f'#{user.id}'
            logger.info(
                '✅ Суточное списание: подписка сумма коп., пользователь',
                subscription_id=subscription.id,
                daily_price=daily_price,
                user_id_display=user_id_display,
            )

            # Синхронизируем с Remnawave (обновляем срок подписки)
            try:
                from app.services.subscription_service import SubscriptionService

                subscription_service = SubscriptionService()
                await subscription_service.create_remnawave_user(
                    db,
                    subscription,
                    reset_traffic=False,
                    reset_reason=None,
                )
            except Exception as e:
                logger.warning('Не удалось обновить Remnawave', error=e)

            # Отправляем уведомление администраторам
            try:
                from app.services.subscription_renewal_service import with_admin_notification_service

                await with_admin_notification_service(
                    lambda svc: svc.send_subscription_extension_notification(
                        db,
                        user,
                        subscription,
                        transaction,
                        1,  # 1 день для суточного тарифа
                        old_end_date,
                        new_end_date=subscription.end_date,
                        balance_after=user.balance_kopeks,
                    )
                )
            except Exception as exc:
                logger.warning('Не удалось отправить админ-уведомление о суточном списании', user_id=user.id, exc=exc)

            # Уведомляем пользователя
            if self._bot:
                await self._notify_daily_charge(user, subscription, daily_price)

            return 'charged'

        except Exception as e:
            await db.rollback()
            logger.error(
                'Ошибка при списании средств для подписки', subscription_id=subscription.id, error=e, exc_info=True
            )
            return 'error'

    async def _notify_daily_charge(self, user, subscription, amount_kopeks: int):
        """Уведомляет пользователя о суточном списании."""
        get_texts(getattr(user, 'language', 'ru'))
        amount_rubles = amount_kopeks / 100
        balance_rubles = user.balance_kopeks / 100

        message = (
            f'💳 <b>Суточное списание</b>\n\n'
            f'Списано: {amount_rubles:.2f} ₽\n'
            f'Остаток баланса: {balance_rubles:.2f} ₽\n\n'
            f'Следующее списание через 24 часа.'
        )

        # Use unified notification delivery service
        try:
            await notification_delivery_service.notify_daily_debit(
                user=user,
                amount_kopeks=amount_kopeks,
                new_balance_kopeks=user.balance_kopeks,
                bot=self._bot,
                telegram_message=message,
            )
        except Exception as e:
            logger.warning('Не удалось отправить уведомление о списании', error=e)

    async def _notify_insufficient_balance(self, user, subscription, required_amount: int):
        """Уведомляет пользователя о недостатке средств."""
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        get_texts(getattr(user, 'language', 'ru'))
        required_rubles = required_amount / 100
        balance_rubles = user.balance_kopeks / 100

        message = (
            f'⚠️ <b>Подписка приостановлена</b>\n\n'
            f'Недостаточно средств для суточной оплаты.\n\n'
            f'Требуется: {required_rubles:.2f} ₽\n'
            f'Баланс: {balance_rubles:.2f} ₽\n\n'
            f'Пополните баланс, чтобы возобновить подписку.'
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='💳 Пополнить баланс', callback_data='menu_balance')],
                [InlineKeyboardButton(text='📱 Моя подписка', callback_data='menu_subscription')],
            ]
        )

        # Use unified notification delivery service
        context = {
            'required_amount': f'{required_rubles:.2f} ₽',
            'current_balance': f'{balance_rubles:.2f} ₽',
        }

        try:
            await notification_delivery_service.send_notification(
                user=user,
                notification_type=NotificationType.DAILY_INSUFFICIENT_FUNDS,
                context=context,
                bot=self._bot,
                telegram_message=message,
                telegram_markup=keyboard,
            )
        except Exception as e:
            logger.warning('Не удалось отправить уведомление о недостатке средств', error=e)

    async def process_traffic_resets(self) -> dict:
        """
        Сбрасывает докупленный трафик у подписок, у которых истёк срок.

        Returns:
            dict: Статистика обработки
        """
        stats = {
            'checked': 0,
            'reset': 0,
            'errors': 0,
        }

        from app.database.models import TrafficPurchase

        try:
            async with distributed_job_lock(_TRAFFIC_EXPIRY_LOCK_ID, name='traffic-topup-expiry') as acquired:
                if not acquired:
                    return stats

                async with AsyncSessionLocal() as db:
                    try:
                        # Находим все истекшие докупки
                        now = datetime.now(UTC)
                        query = select(TrafficPurchase).where(TrafficPurchase.expires_at <= now)
                        result = await db.execute(query)
                        expired_purchases = result.scalars().all()
                        stats['checked'] = len(expired_purchases)

                        # Группируем по подпискам для обновления
                        subscriptions_to_update: dict[int, list[TrafficPurchase]] = {}
                        for purchase in expired_purchases:
                            if purchase.subscription_id not in subscriptions_to_update:
                                subscriptions_to_update[purchase.subscription_id] = []
                            subscriptions_to_update[purchase.subscription_id].append(purchase)

                        # Удаляем истекшие докупки и обновляем подписки
                        for subscription_id in subscriptions_to_update:
                            try:
                                stats['reset'] += await self._reset_subscription_traffic(db, subscription_id)
                            except Exception as e:
                                await db.rollback()
                                logger.error(
                                    'Ошибка сброса трафика подписки',
                                    subscription_id=subscription_id,
                                    error=e,
                                    exc_info=True,
                                )
                                stats['errors'] += 1
                                break
                    except Exception as e:
                        logger.error('Ошибка при обработке сброса трафика', error=e, exc_info=True)
                        await db.rollback()

        except Exception as e:
            logger.error('Ошибка при получении подписок для сброса трафика', error=e, exc_info=True)

        return stats

    async def _reset_subscription_traffic(self, db: AsyncSession, subscription_id: int) -> int:
        """Сбрасывает истекшие докупки трафика у подписки."""
        # Получаем подписку
        subscription_query = (
            select(Subscription)
            .options(selectinload(Subscription.tariff))
            .where(Subscription.id == subscription_id)
            .with_for_update()
        )
        subscription_result = await db.execute(subscription_query)
        subscription = subscription_result.scalar_one_or_none()

        if not subscription:
            return 0

        now = datetime.now(UTC)
        old_limit = subscription.traffic_limit_gb or 0
        old_purchased = subscription.purchased_traffic_gb or 0
        expired_purchases = await remove_expired_traffic_purchases(db, subscription, now=now)
        if not expired_purchases:
            return 0
        total_expired_gb = sum(p.traffic_gb for p in expired_purchases)
        new_purchased = subscription.purchased_traffic_gb
        base_limit = subscription.traffic_limit_gb - new_purchased if subscription.traffic_limit_gb > 0 else 0

        subscription.updated_at = datetime.now(UTC)

        await db.flush()

        # Commit quota and expired rows only after panel synchronization succeeds.
        user = await get_user_by_id(db, subscription.user_id) if subscription.user_id else None
        if user and user.remnawave_uuid:
            from app.services.subscription_service import SubscriptionService

            subscription_service = SubscriptionService()
            updated_user = await subscription_service.update_remnawave_user(db, subscription, commit=False)
            if updated_user is None:
                await db.rollback()
                raise RuntimeError('RemnaWave rejected traffic top-up expiry update')

        await db.commit()

        logger.info(
            '🔄 Сброс истекших докупок: подписка было ГБ (базовый: ГБ, докуплено: ГБ), стало ГБ (базовый: ГБ, докуплено: ГБ), убрано ГБ из покупок',
            subscription_id=subscription.id,
            old_limit=old_limit,
            base_limit=base_limit,
            old_purchased=old_purchased,
            traffic_limit_gb=subscription.traffic_limit_gb,
            base_limit_2=base_limit,
            new_purchased=new_purchased,
            total_expired_gb=total_expired_gb,
            expired_purchases_count=len(expired_purchases),
        )

        # Уведомляем пользователя
        if self._bot and subscription.user_id:
            user = await get_user_by_id(db, subscription.user_id)
            if user:
                await self._notify_traffic_reset(user, subscription, total_expired_gb)

        return len(expired_purchases)

    async def _notify_traffic_reset(self, user: User, subscription: Subscription, reset_gb: int):
        """Уведомляет пользователя о сбросе докупленного трафика."""
        message = (
            f'ℹ️ <b>Сброс докупленного трафика</b>\n\n'
            f'Ваш докупленный трафик ({reset_gb} ГБ) был сброшен, '
            f'так как прошло 30 дней с момента первой докупки.\n\n'
            f'Текущий лимит трафика: {subscription.traffic_limit_gb} ГБ\n\n'
            f'Вы можете докупить трафик снова в любое время.'
        )

        context = {
            'reset_gb': reset_gb,
            'current_limit_gb': subscription.traffic_limit_gb,
        }

        # Use unified notification delivery service
        try:
            await notification_delivery_service.send_notification(
                user=user,
                notification_type=NotificationType.TRAFFIC_RESET,
                context=context,
                bot=self._bot,
                telegram_message=message,
            )
        except Exception as e:
            logger.warning('Не удалось отправить уведомление о сбросе трафика', error=e)

    async def start_monitoring(self):
        """Запускает периодическую проверку суточных подписок и сброса трафика."""
        self._running = True
        daily_interval_seconds = self.get_check_interval_minutes() * 60
        traffic_interval_seconds = self.get_traffic_reset_check_interval_seconds()
        last_daily_check_at: datetime | None = None
        last_traffic_reset_check_at: datetime | None = None

        logger.info(
            '🔄 Запуск сервиса суточных подписок',
            interval_minutes=self.get_check_interval_minutes(),
            traffic_reset_interval_seconds=traffic_interval_seconds,
        )

        while self._running:
            try:
                # Обработка суточных списаний
                now = datetime.now(UTC)
                should_process_daily = self.is_daily_charges_enabled() and (
                    last_daily_check_at is None or (now - last_daily_check_at).total_seconds() >= daily_interval_seconds
                )
                should_process_traffic = self.is_traffic_resets_enabled() and (
                    last_traffic_reset_check_at is None
                    or (now - last_traffic_reset_check_at).total_seconds() >= traffic_interval_seconds
                )

                if should_process_daily:
                    stats = await self.process_daily_charges()
                    last_daily_check_at = now
                else:
                    stats = {'checked': 0, 'charged': 0, 'suspended': 0, 'errors': 0}

                if stats['charged'] > 0 or stats['suspended'] > 0:
                    logger.info(
                        '📊 Суточные списания: проверено=, списано=, приостановлено=, ошибок',
                        stats=stats['checked'],
                        stats_2=stats['charged'],
                        stats_3=stats['suspended'],
                        stats_4=stats['errors'],
                    )

                # Обработка сброса докупленного трафика
                if should_process_traffic:
                    traffic_stats = await self.process_traffic_resets()
                    last_traffic_reset_check_at = now
                else:
                    traffic_stats = {'checked': 0, 'reset': 0, 'errors': 0}
                if traffic_stats['reset'] > 0:
                    logger.info(
                        '📊 Сброс трафика: проверено=, сброшено=, ошибок',
                        traffic_stats=traffic_stats['checked'],
                        traffic_stats_2=traffic_stats['reset'],
                        traffic_stats_3=traffic_stats['errors'],
                    )
            except Exception as e:
                logger.error('Ошибка в цикле проверки суточных подписок', error=e, exc_info=True)

            sleep_seconds = min(
                daily_interval_seconds if self.is_daily_charges_enabled() else traffic_interval_seconds,
                traffic_interval_seconds if self.is_traffic_resets_enabled() else daily_interval_seconds,
            )
            await asyncio.sleep(max(10, sleep_seconds))

    def stop_monitoring(self):
        """Останавливает периодическую проверку."""
        self._running = False
        logger.info('⏹️ Сервис суточных подписок остановлен')


# Глобальный экземпляр сервиса
daily_subscription_service = DailySubscriptionService()


__all__ = ['DailySubscriptionService', 'daily_subscription_service']
