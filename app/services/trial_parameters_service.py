from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.tariff import get_tariff_by_id, get_trial_tariff
from app.database.models import Tariff


logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class TrialParameters:
    duration_days: int
    traffic_limit_gb: int
    device_limit: int
    connected_squads: list[str]
    tariff_id: int | None
    tariff: Tariff | None


async def resolve_trial_parameters(
    db: AsyncSession,
    *,
    device_limit_override: int | None = None,
    include_tariff: bool | None = None,
) -> TrialParameters:
    """Resolve one consistent set of limits for every trial activation entrypoint.

    Dedicated trial settings own duration, traffic, and device limits. A selected
    trial tariff only supplies its server squads and tariff identity.
    """
    trial_tariff: Tariff | None = None
    should_load_tariff = settings.is_tariffs_mode() if include_tariff is None else include_tariff

    if should_load_tariff:
        try:
            trial_tariff = await get_trial_tariff(db)
            if trial_tariff is None:
                trial_tariff_id = settings.get_trial_tariff_id()
                if trial_tariff_id > 0:
                    trial_tariff = await get_tariff_by_id(db, trial_tariff_id)
                    if trial_tariff is not None and not trial_tariff.is_active:
                        trial_tariff = None
        except Exception as error:
            logger.warning('Failed to resolve trial tariff, using global trial limits', error=error)

    return TrialParameters(
        duration_days=settings.TRIAL_DURATION_DAYS,
        traffic_limit_gb=settings.TRIAL_TRAFFIC_LIMIT_GB,
        device_limit=device_limit_override if device_limit_override is not None else settings.TRIAL_DEVICE_LIMIT,
        connected_squads=list(trial_tariff.allowed_squads or []) if trial_tariff is not None else [],
        tariff_id=trial_tariff.id if trial_tariff is not None else None,
        tariff=trial_tariff,
    )
