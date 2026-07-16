from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.server_squad import get_server_squad_by_uuid
from app.database.models import Subscription, User
from app.services.metered_traffic_policy import get_customer_squad_uuids
from app.services.remnawave_service import (
    RemnaWaveConfigurationError,
    RemnaWaveService,
)
from app.services.subscription_service import SubscriptionService

from ...schemas.miniapp import MiniAppConnectedServer, MiniAppDevice
from ..miniapp_format_helpers import parse_datetime_string
from ..miniapp_misc_helpers import is_remnawave_configured


logger = structlog.get_logger(__name__)


async def resolve_connected_servers(
    db: AsyncSession,
    squad_uuids: list[str],
) -> list[MiniAppConnectedServer]:
    squad_uuids = get_customer_squad_uuids(squad_uuids)
    if not squad_uuids:
        return []

    resolved: dict[str, str] = {}
    missing: list[str] = []

    for squad_uuid in squad_uuids:
        if squad_uuid in resolved:
            continue
        server = await get_server_squad_by_uuid(db, squad_uuid)
        if server and server.display_name:
            resolved[squad_uuid] = server.display_name
        else:
            missing.append(squad_uuid)

    if missing:
        try:
            service = RemnaWaveService()
            if service.is_configured:
                squads = await service.get_all_squads()
                for squad in squads:
                    uuid = squad.get('uuid')
                    name = squad.get('name')
                    if uuid in missing and name:
                        resolved[uuid] = name
        except RemnaWaveConfigurationError:
            logger.debug('RemnaWave is not configured; skipping server name enrichment')
        except Exception as error:  # pragma: no cover - defensive logging
            logger.warning('Failed to resolve server names from RemnaWave', error=error)

    connected_servers: list[MiniAppConnectedServer] = []
    for squad_uuid in squad_uuids:
        name = resolved.get(squad_uuid, squad_uuid)
        connected_servers.append(MiniAppConnectedServer(uuid=squad_uuid, name=name))

    return connected_servers


async def load_devices_info(user: User) -> tuple[int, list[MiniAppDevice]]:
    remnawave_uuid = getattr(user, 'remnawave_uuid', None)
    if not remnawave_uuid:
        return 0, []

    try:
        service = RemnaWaveService()
    except Exception as error:  # pragma: no cover - defensive logging
        logger.warning('Failed to initialise RemnaWave service', error=error)
        return 0, []

    if not service.is_configured:
        return 0, []

    try:
        async with service.get_api_client() as api:
            response = await api.get_user_devices(remnawave_uuid)
    except RemnaWaveConfigurationError:
        logger.debug('RemnaWave configuration missing while loading devices')
        return 0, []
    except Exception as error:  # pragma: no cover - defensive logging
        logger.warning('Failed to load devices from RemnaWave', error=error)
        return 0, []

    total_devices = int(response.get('total') or 0)
    devices_payload = response.get('devices') or []

    devices: list[MiniAppDevice] = []
    for device in devices_payload:
        hwid = device.get('hwid') or device.get('deviceId') or device.get('id')
        platform = device.get('platform') or device.get('platformType')
        model = device.get('deviceModel') or device.get('model') or device.get('name')
        app_version = device.get('appVersion') or device.get('version')
        last_seen_raw = (
            device.get('updatedAt') or device.get('lastSeen') or device.get('lastActiveAt') or device.get('createdAt')
        )
        last_ip = device.get('ip') or device.get('ipAddress')

        devices.append(
            MiniAppDevice(
                hwid=hwid,
                platform=platform,
                device_model=model,
                app_version=app_version,
                last_seen=parse_datetime_string(last_seen_raw),
                last_ip=last_ip,
            )
        )

    if total_devices == 0:
        total_devices = len(devices)

    return total_devices, devices


async def load_subscription_links(
    subscription: Subscription,
) -> dict[str, Any]:
    if not subscription.remnawave_short_uuid or not is_remnawave_configured():
        return {}

    try:
        service = SubscriptionService()
        info = await service.get_subscription_info(subscription.remnawave_short_uuid)
    except Exception as error:  # pragma: no cover - defensive logging
        logger.warning('Failed to load subscription info from RemnaWave', error=error)
        return {}

    if not info:
        return {}

    payload: dict[str, Any] = {
        'links': list(info.links or []),
        'ss_conf_links': dict(info.ss_conf_links or {}),
        'subscription_url': info.subscription_url,
        'happ': info.happ,
        'happ_link': getattr(info, 'happ_link', None),
        'happ_crypto_link': getattr(info, 'happ_crypto_link', None),
    }

    return payload
