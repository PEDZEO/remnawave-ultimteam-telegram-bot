from dataclasses import dataclass
from datetime import UTC, date, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.subscription import extend_subscription, get_subscription_by_user_id
from app.database.crud.user import add_user_balance
from app.database.models import TapRewardProgress, TransactionType, User
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

    async def record_taps(self, db: AsyncSession, user: User, count: int) -> TapRewardResult:
        threshold = self._threshold()
        daily_limit = self._daily_limit()

        if not settings.TAP_REWARDS_ENABLED:
            return self._empty_result(enabled=False, threshold=threshold, daily_limit=daily_limit)

        safe_count = max(1, min(int(count or 1), self.max_taps_per_request))
        now = datetime.now(UTC)

        progress = await self._get_or_create_progress(db, user.id)
        self._reset_daily_counter_if_needed(progress, today=now.date())

        progress.total_taps = max(0, int(progress.total_taps or 0)) + safe_count
        progress.last_tap_at = now
        progress.updated_at = now

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
                threshold=threshold,
                daily_limit=daily_limit,
                now=now,
            )

        return await self._grant_subscription_reward(
            db,
            user,
            progress,
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

        self._reset_daily_counter_if_needed(progress, today=datetime.now(UTC).date())
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

    async def _grant_balance_reward(
        self,
        db: AsyncSession,
        user: User,
        progress: TapRewardProgress,
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
        message = f'Подарок за тапы: +{self._format_rubles(amount)}'
        return self._build_result(
            progress,
            threshold=threshold,
            daily_limit=daily_limit,
            reward_granted=True,
            reward_type=REWARD_TYPE_BALANCE,
            reward_value=amount,
            message=message,
            balance_kopeks=user.balance_kopeks,
        )

    async def _grant_subscription_reward(
        self,
        db: AsyncSession,
        user: User,
        progress: TapRewardProgress,
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
        await db.refresh(subscription)

        message = f'Подарок за тапы: +{days} дн. к подписке'
        return self._build_result(
            progress,
            threshold=threshold,
            daily_limit=daily_limit,
            reward_granted=True,
            reward_type=REWARD_TYPE_SUBSCRIPTION_DAYS,
            reward_value=days,
            message=message,
            subscription_end_date=subscription.end_date,
        )

    @staticmethod
    def _threshold() -> int:
        return max(1, int(settings.TAP_REWARDS_THRESHOLD or 1))

    @staticmethod
    def _daily_limit() -> int:
        return max(0, int(settings.TAP_REWARDS_DAILY_REWARD_LIMIT or 0))

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

    @staticmethod
    def _has_unclaimed_reward(progress: TapRewardProgress, threshold: int) -> bool:
        total_taps = max(0, int(progress.total_taps or 0))
        reward_count = max(0, int(progress.reward_count or 0))
        return total_taps // threshold > reward_count

    @staticmethod
    def _daily_limit_reached(progress: TapRewardProgress, daily_limit: int) -> bool:
        return daily_limit > 0 and int(progress.daily_reward_count or 0) >= daily_limit

    @staticmethod
    def _mark_reward_granted(progress: TapRewardProgress, *, now: datetime) -> None:
        progress.reward_count = max(0, int(progress.reward_count or 0)) + 1
        progress.daily_reward_count = max(0, int(progress.daily_reward_count or 0)) + 1
        progress.last_reward_at = now
        progress.updated_at = now

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
        reward_count = max(0, int(progress.reward_count or 0))
        earned_rewards = total_taps // threshold
        if earned_rewards > reward_count:
            progress_taps = threshold
            taps_until_next = 0
        else:
            raw_progress = total_taps - reward_count * threshold
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
