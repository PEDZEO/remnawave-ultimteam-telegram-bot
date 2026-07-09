from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.cabinet.dependencies import get_cabinet_db, get_current_cabinet_user
from app.database.models import User
from app.services.tap_reward_service import tap_reward_service
from app.utils.cache import RateLimitCache


router = APIRouter(prefix='/tap-rewards', tags=['Cabinet Tap Rewards'])


class TapRewardRequest(BaseModel):
    # One authenticated request represents one physical tap. Batch values made rewards trivial to forge.
    count: int = Field(default=1, ge=1, le=1)


class TapRewardResponse(BaseModel):
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
    reward_granted: bool
    reward_type: str | None = None
    reward_value: int | None = None
    message: str | None = None
    balance_kopeks: int | None = None
    subscription_end_date: datetime | None = None


@router.get('/progress', response_model=TapRewardResponse)
async def get_tap_reward_progress(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    result = await tap_reward_service.get_progress(db, user)
    return TapRewardResponse(**asdict(result))


@router.post('/tap', response_model=TapRewardResponse)
async def record_tap_reward(
    payload: TapRewardRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    is_limited = await RateLimitCache.is_rate_limited(
        user.id,
        'tap_reward',
        limit=20,
        window=1,
        fail_closed=True,
    )
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Too many taps. Please slow down.',
        )

    result = await tap_reward_service.record_taps(db, user, payload.count)
    return TapRewardResponse(**asdict(result))
