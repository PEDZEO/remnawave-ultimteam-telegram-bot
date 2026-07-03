from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import escape
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.subscription import extend_subscription, get_subscription_by_user_id
from app.database.crud.user import add_user_balance
from app.database.models import TapRewardDailyStats, TapRewardProgress, TransactionType, User
from app.services.subscription_service import SubscriptionService


logger = structlog.get_logger(__name__)

REWARD_TYPE_BALANCE = 'balance'
REWARD_TYPE_SUBSCRIPTION_DAYS = 'subscription_days'


@dataclass(slots=True)
class TapRewardResult:
    enabled: bool
    total_taps: int
    progress_taps: int
    threshold: int
    taps_until_next: int
    streak_timeout_seconds: int
    rewards_granted_total: int
    daily_reward_limit: int
    daily_rewards_granted: int
    daily_limit_reached: bool
    reward_granted: bool = False
    reward_type: str | None = None
    reward_value: int | None = None
    message: str | None = None
    balance_kopeks: int | None = None
    subscription_end_date: datetime | None = None


class TapRewardService:
    max_taps_per_request = 25
    moscow_tz = ZoneInfo('Europe/Moscow')

    async def record_taps(self, db: AsyncSession, user: User, count: int) -> TapRewardResult:
        threshold = self._threshold()
        daily_limit = self._daily_limit()

        if not settings.TAP_REWARDS_ENABLED:
            return self._empty_result(enabled=False, threshold=threshold, daily_limit=daily_limit)

        safe_count = max(1, min(int(count or 1), self.max_taps_per_request))
        now = datetime.now(UTC)
        stat_date = now.astimezone(self.moscow_tz).date()

        progress = await self._get_or_create_progress(db, user.id)
        daily_stats = await self._get_or_create_daily_stats(db, user.id, stat_date)
        self._reset_daily_counter_if_needed(progress, today=now.date())
        self._reset_streak_if_needed(progress, now=now)

        progress.total_taps = max(0, int(progress.total_taps or 0)) + safe_count
        progress.streak_taps = max(0, int(progress.streak_taps or 0)) + safe_count
        progress.last_tap_at = now
        progress.updated_at = now
        self._mark_daily_taps(daily_stats, safe_count, now=now)

        can_grant = self._has_unclaimed_reward(progress, threshold)
        daily_limit_reached = self._daily_limit_reached(progress, daily_limit)

        if not can_grant or daily_limit_reached:
            await db.commit()
            await db.refresh(progress)
            return self._build_result(
                progress,
                threshold=threshold,
                daily_limit=daily_limit,
                reward_granted=False,
            )

        reward_type = self._reward_type()
        if reward_type == REWARD_TYPE_BALANCE:
            return await self._grant_balance_reward(
                db,
                user,
                progress,
                daily_stats,
                threshold=threshold,
                daily_limit=daily_limit,
                now=now,
            )

        return await self._grant_subscription_reward(
            db,
            user,
            progress,
            daily_stats,
            threshold=threshold,
            daily_limit=daily_limit,
            now=now,
        )

    async def get_progress(self, db: AsyncSession, user: User) -> TapRewardResult:
        threshold = self._threshold()
        daily_limit = self._daily_limit()

        if not settings.TAP_REWARDS_ENABLED:
            return self._empty_result(enabled=False, threshold=threshold, daily_limit=daily_limit)

        result = await db.execute(select(TapRewardProgress).where(TapRewardProgress.user_id == user.id))
        progress = result.scalar_one_or_none()
        if progress is None:
            return self._empty_result(enabled=True, threshold=threshold, daily_limit=daily_limit)

        now = datetime.now(UTC)
        self._reset_daily_counter_if_needed(progress, today=now.date())
        self._reset_streak_if_needed(progress, now=now)
        await db.commit()
        await db.refresh(progress)
        return self._build_result(progress, threshold=threshold, daily_limit=daily_limit)

    async def _get_or_create_progress(self, db: AsyncSession, user_id: int) -> TapRewardProgress:
        result = await db.execute(
            select(TapRewardProgress)
            .where(TapRewardProgress.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        progress = result.scalar_one_or_none()
        if progress is not None:
            return progress

        progress = TapRewardProgress(user_id=user_id)
        db.add(progress)
        try:
            await db.flush()
            return progress
        except IntegrityError:
            await db.rollback()
            result = await db.execute(
                select(TapRewardProgress)
                .where(TapRewardProgress.user_id == user_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            return result.scalar_one()

    async def _get_or_create_daily_stats(
        self,
        db: AsyncSession,
        user_id: int,
        stat_date: date,
    ) -> TapRewardDailyStats:
        result = await db.execute(
            select(TapRewardDailyStats)
            .where(TapRewardDailyStats.user_id == user_id, TapRewardDailyStats.stat_date == stat_date)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        daily_stats = result.scalar_one_or_none()
        if daily_stats is not None:
            return daily_stats

        daily_stats = TapRewardDailyStats(user_id=user_id, stat_date=stat_date)
        db.add(daily_stats)
        try:
            await db.flush()
            return daily_stats
        except IntegrityError:
            await db.rollback()
            result = await db.execute(
                select(TapRewardDailyStats)
                .where(TapRewardDailyStats.user_id == user_id, TapRewardDailyStats.stat_date == stat_date)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            return result.scalar_one()

    async def _grant_balance_reward(
        self,
        db: AsyncSession,
        user: User,
        progress: TapRewardProgress,
        daily_stats: TapRewardDailyStats,
        *,
        threshold: int,
        daily_limit: int,
        now: datetime,
    ) -> TapRewardResult:
        amount = max(0, int(settings.TAP_REWARDS_BALANCE_KOPEKS or 0))
        if amount <= 0:
            await db.commit()
            await db.refresh(progress)
            return self._build_result(
                progress,
                threshold=threshold,
                daily_limit=daily_limit,
                message='Подарок за тапы не настроен: сумма баланса равна 0.',
            )

        self._mark_reward_granted(progress, now=now)
        self._mark_daily_reward(
            daily_stats,
            reward_type=REWARD_TYPE_BALANCE,
            reward_value=amount,
            now=now,
        )
        success = await add_user_balance(
            db,
            user,
            amount,
            description='Подарок за тапы',
            create_transaction=True,
            transaction_type=TransactionType.TAP_REWARD,
        )
        if not success:
            logger.warning('Failed to grant tap balance reward', user_id=user.id, amount_kopeks=amount)
            return self._empty_result(enabled=True, threshold=threshold, daily_limit=daily_limit)

        await db.refresh(user)
        await db.refresh(progress)
        await db.refresh(daily_stats)
        message = f'Подарок за тапы: +{self._format_rubles(amount)}'
        result = self._build_result(
            progress,
            threshold=threshold,
            daily_limit=daily_limit,
            reward_granted=True,
            reward_type=REWARD_TYPE_BALANCE,
            reward_value=amount,
            message=message,
            balance_kopeks=user.balance_kopeks,
        )
        await self._send_reward_admin_notification(user, progress, daily_stats, result)
        return result

    async def _grant_subscription_reward(
        self,
        db: AsyncSession,
        user: User,
        progress: TapRewardProgress,
        daily_stats: TapRewardDailyStats,
        *,
        threshold: int,
        daily_limit: int,
        now: datetime,
    ) -> TapRewardResult:
        days = max(0, int(settings.TAP_REWARDS_SUBSCRIPTION_DAYS or 0))
        if days <= 0:
            await db.commit()
            await db.refresh(progress)
            return self._build_result(
                progress,
                threshold=threshold,
                daily_limit=daily_limit,
                message='Подарок за тапы не настроен: количество дней равно 0.',
            )

        subscription = await get_subscription_by_user_id(db, user.id)
        if subscription is None:
            await db.commit()
            await db.refresh(progress)
            return self._build_result(
                progress,
                threshold=threshold,
                daily_limit=daily_limit,
                message='Для подарка днями нужна подписка.',
            )

        self._mark_reward_granted(progress, now=now)
        self._mark_daily_reward(
            daily_stats,
            reward_type=REWARD_TYPE_SUBSCRIPTION_DAYS,
            reward_value=days,
            now=now,
        )
        subscription = await extend_subscription(db, subscription, days, commit=False)

        try:
            subscription_service = SubscriptionService()
            if user.remnawave_uuid:
                await subscription_service.update_remnawave_user(db, subscription, commit=False)
            else:
                await subscription_service.create_remnawave_user(db, subscription, commit=False)
        except Exception as error:
            logger.warning('Failed to sync tap subscription reward with RemnaWave', user_id=user.id, error=error)

        await db.commit()
        await db.refresh(progress)
        await db.refresh(daily_stats)
        await db.refresh(subscription)

        message = f'Подарок за тапы: +{days} дн. к подписке'
        result = self._build_result(
            progress,
            threshold=threshold,
            daily_limit=daily_limit,
            reward_granted=True,
            reward_type=REWARD_TYPE_SUBSCRIPTION_DAYS,
            reward_value=days,
            message=message,
            subscription_end_date=subscription.end_date,
        )
        await self._send_reward_admin_notification(user, progress, daily_stats, result)
        return result

    @staticmethod
    def _threshold() -> int:
        return max(1, int(settings.TAP_REWARDS_THRESHOLD or 1))

    @staticmethod
    def _daily_limit() -> int:
        return max(0, int(settings.TAP_REWARDS_DAILY_REWARD_LIMIT or 0))

    @staticmethod
    def _streak_timeout_seconds() -> int:
        return max(0, int(settings.TAP_REWARDS_STREAK_TIMEOUT_SECONDS or 0))

    @staticmethod
    def _reward_type() -> str:
        if settings.TAP_REWARDS_REWARD_TYPE == REWARD_TYPE_BALANCE:
            return REWARD_TYPE_BALANCE
        return REWARD_TYPE_SUBSCRIPTION_DAYS

    @staticmethod
    def _reset_daily_counter_if_needed(progress: TapRewardProgress, *, today: date) -> None:
        if progress.daily_reward_date == today:
            return
        progress.daily_reward_date = today
        progress.daily_reward_count = 0

    @classmethod
    def _reset_streak_if_needed(cls, progress: TapRewardProgress, *, now: datetime) -> None:
        timeout_seconds = cls._streak_timeout_seconds()
        if timeout_seconds <= 0 or progress.last_tap_at is None:
            return

        last_tap_at = progress.last_tap_at
        if last_tap_at.tzinfo is None:
            last_tap_at = last_tap_at.replace(tzinfo=UTC)

        if (now - last_tap_at).total_seconds() <= timeout_seconds:
            return

        progress.streak_taps = 0
        progress.streak_reward_count = 0
        progress.updated_at = now

    @staticmethod
    def _has_unclaimed_reward(progress: TapRewardProgress, threshold: int) -> bool:
        streak_taps = max(0, int(progress.streak_taps or 0))
        streak_reward_count = max(0, int(progress.streak_reward_count or 0))
        return streak_taps // threshold > streak_reward_count

    @staticmethod
    def _daily_limit_reached(progress: TapRewardProgress, daily_limit: int) -> bool:
        return daily_limit > 0 and int(progress.daily_reward_count or 0) >= daily_limit

    @staticmethod
    def _mark_reward_granted(progress: TapRewardProgress, *, now: datetime) -> None:
        progress.reward_count = max(0, int(progress.reward_count or 0)) + 1
        progress.streak_reward_count = max(0, int(progress.streak_reward_count or 0)) + 1
        progress.daily_reward_count = max(0, int(progress.daily_reward_count or 0)) + 1
        progress.last_reward_at = now
        progress.updated_at = now

    @staticmethod
    def _mark_daily_taps(daily_stats: TapRewardDailyStats, count: int, *, now: datetime) -> None:
        daily_stats.tap_count = max(0, int(daily_stats.tap_count or 0)) + max(0, int(count or 0))
        daily_stats.last_tap_at = now
        daily_stats.updated_at = now

    @staticmethod
    def _mark_daily_reward(
        daily_stats: TapRewardDailyStats,
        *,
        reward_type: str,
        reward_value: int,
        now: datetime,
    ) -> None:
        daily_stats.reward_count = max(0, int(daily_stats.reward_count or 0)) + 1
        if reward_type == REWARD_TYPE_BALANCE:
            daily_stats.balance_reward_kopeks = max(0, int(daily_stats.balance_reward_kopeks or 0)) + max(
                0,
                int(reward_value or 0),
            )
        elif reward_type == REWARD_TYPE_SUBSCRIPTION_DAYS:
            daily_stats.subscription_reward_days = max(
                0,
                int(daily_stats.subscription_reward_days or 0),
            ) + max(0, int(reward_value or 0))
        daily_stats.last_reward_at = now
        daily_stats.updated_at = now

    async def _send_reward_admin_notification(
        self,
        user: User,
        progress: TapRewardProgress,
        daily_stats: TapRewardDailyStats,
        result: TapRewardResult,
    ) -> None:
        if not getattr(settings, 'TAP_REWARDS_ADMIN_NOTIFICATIONS_ENABLED', True):
            return

        try:
            from app.services.subscription_renewal_service import with_admin_notification_service

            text = self._build_reward_admin_message(user, progress, daily_stats, result)
            await with_admin_notification_service(lambda service: service.send_admin_notification(text))
        except Exception as error:  # pragma: no cover - defensive notification guard
            logger.warning('Failed to send tap reward admin notification', user_id=user.id, error=error)

    @classmethod
    def _build_reward_admin_message(
        cls,
        user: User,
        progress: TapRewardProgress,
        daily_stats: TapRewardDailyStats,
        result: TapRewardResult,
    ) -> str:
        stat_date = daily_stats.stat_date.strftime('%d.%m.%Y') if daily_stats.stat_date else 'unknown'
        reward_label = cls._format_reward_label(result.reward_type, result.reward_value)
        streak_taps = max(0, int(progress.streak_taps or 0))
        threshold = max(1, int(result.threshold or 1))

        return '\n'.join(
            [
                '🎁 <b>Подарок за тапы выдан</b>',
                '',
                f'👤 Пользователь: <b>{cls._format_user_label(user)}</b>',
                f'🎯 Подарок: <b>{escape(reward_label)}</b>',
                f'👆 Тапов сегодня: <b>{max(0, int(daily_stats.tap_count or 0))}</b>',
                f'🎁 Подарков сегодня: <b>{max(0, int(daily_stats.reward_count or 0))}</b>',
                f'📈 Текущий стрик: <b>{streak_taps}/{threshold}</b>',
                f'🏁 Всего подарков пользователю: <b>{max(0, int(progress.reward_count or 0))}</b>',
                f'📅 Дата статистики: <b>{escape(stat_date)} МСК</b>',
            ]
        )

    @staticmethod
    def _format_user_label(user: User) -> str:
        parts = [f'ID {getattr(user, "id", "unknown")}']
        telegram_id = getattr(user, 'telegram_id', None)
        username = getattr(user, 'username', None)
        email = getattr(user, 'email', None)

        if telegram_id:
            parts.append(f'TG {telegram_id}')
        if username:
            username_text = str(username)
            parts.append(username_text if username_text.startswith('@') else f'@{username_text}')
        if email:
            parts.append(str(email))

        return escape(' / '.join(parts))

    @classmethod
    def _format_reward_label(cls, reward_type: str | None, reward_value: int | None) -> str:
        value = max(0, int(reward_value or 0))
        if reward_type == REWARD_TYPE_BALANCE:
            return cls._format_rubles(value)
        if reward_type == REWARD_TYPE_SUBSCRIPTION_DAYS:
            return f'{value} дн. к подписке'
        return 'Подарок'

    @classmethod
    def _build_result(
        cls,
        progress: TapRewardProgress,
        *,
        threshold: int,
        daily_limit: int,
        reward_granted: bool = False,
        reward_type: str | None = None,
        reward_value: int | None = None,
        message: str | None = None,
        balance_kopeks: int | None = None,
        subscription_end_date: datetime | None = None,
    ) -> TapRewardResult:
        total_taps = max(0, int(progress.total_taps or 0))
        streak_taps = max(0, int(progress.streak_taps or 0))
        reward_count = max(0, int(progress.reward_count or 0))
        streak_reward_count = max(0, int(progress.streak_reward_count or 0))
        earned_streak_rewards = streak_taps // threshold
        if earned_streak_rewards > streak_reward_count:
            progress_taps = threshold
            taps_until_next = 0
        else:
            raw_progress = streak_taps - streak_reward_count * threshold
            progress_taps = max(0, min(threshold, raw_progress))
            taps_until_next = max(0, threshold - progress_taps)

        daily_rewards = max(0, int(progress.daily_reward_count or 0))
        daily_limit_reached = daily_limit > 0 and daily_rewards >= daily_limit

        return TapRewardResult(
            enabled=True,
            total_taps=total_taps,
            progress_taps=progress_taps,
            threshold=threshold,
            taps_until_next=taps_until_next,
            streak_timeout_seconds=cls._streak_timeout_seconds(),
            rewards_granted_total=reward_count,
            daily_reward_limit=daily_limit,
            daily_rewards_granted=daily_rewards,
            daily_limit_reached=daily_limit_reached,
            reward_granted=reward_granted,
            reward_type=reward_type,
            reward_value=reward_value,
            message=message,
            balance_kopeks=balance_kopeks,
            subscription_end_date=subscription_end_date,
        )

    @staticmethod
    def _empty_result(*, enabled: bool, threshold: int, daily_limit: int) -> TapRewardResult:
        return TapRewardResult(
            enabled=enabled,
            total_taps=0,
            progress_taps=0,
            threshold=threshold,
            taps_until_next=threshold,
            streak_timeout_seconds=TapRewardService._streak_timeout_seconds(),
            rewards_granted_total=0,
            daily_reward_limit=daily_limit,
            daily_rewards_granted=0,
            daily_limit_reached=False,
        )

    @staticmethod
    def _format_rubles(kopeks: int) -> str:
        rubles = kopeks / 100
        if rubles.is_integer():
            return f'{int(rubles)} ₽'
        return f'{rubles:.2f} ₽'


tap_reward_service = TapRewardService()
