"""Helper functions for subscription app-config/deep-link rendering."""

import base64
import re
from typing import Any

import structlog

from app.config import settings
from app.services.remnawave_service import RemnaWaveService
from app.services.system_settings_service import bot_configuration_service


logger = structlog.get_logger(__name__)


def _get_remnawave_config_uuid() -> str | None:
    """Get RemnaWave config UUID from system settings or env."""
    try:
        return bot_configuration_service.get_current_value('CABINET_REMNA_SUB_CONFIG')
    except Exception:
        return settings.CABINET_REMNA_SUB_CONFIG


def _extract_scheme_from_buttons(buttons: list[dict[str, Any]]) -> tuple[str, bool]:
    """Extract URL scheme from buttons list.

    Returns:
        Tuple of (scheme, uses_crypto_link).
        uses_crypto_link=True when the template is {{HAPP_CRYPT4_LINK}},
        meaning subscription_crypto_link should be used as payload.
    """
    for btn in buttons:
        if not isinstance(btn, dict):
            continue
        link = btn.get('link', '') or btn.get('url', '') or btn.get('buttonLink', '')
        if not link:
            continue
        link_upper = link.upper()

        if '{{HAPP_CRYPT4_LINK}}' in link_upper or 'HAPP_CRYPT4_LINK' in link_upper:
            scheme = re.sub(r'\{\{HAPP_CRYPT4_LINK\}\}', '', link, flags=re.IGNORECASE)
            if scheme and '://' in scheme:
                return scheme, True

        if '{{SUBSCRIPTION_LINK}}' in link_upper or 'SUBSCRIPTION_LINK' in link_upper:
            scheme = re.sub(r'\{\{SUBSCRIPTION_LINK\}\}', '', link, flags=re.IGNORECASE)
            if scheme and '://' in scheme:
                return scheme, False

        btn_type = btn.get('type', '')
        if btn_type == 'subscriptionLink' and '://' in link and not link.startswith('http'):
            scheme = link.split('{{')[0] if '{{' in link else link
            if scheme and '://' in scheme:
                return scheme, False
    return '', False


def _get_url_scheme_for_app(app: dict[str, Any]) -> tuple[str, bool]:
    """Get URL scheme for app - from config, buttons, or fallback by name."""
    scheme = str(app.get('urlScheme', '')).strip()
    if scheme:
        uses_crypto = bool(app.get('usesCryptoLink', False))
        return scheme, uses_crypto

    blocks = app.get('blocks', [])
    for block in blocks:
        if not isinstance(block, dict):
            continue
        buttons = block.get('buttons', [])
        scheme, uses_crypto = _extract_scheme_from_buttons(buttons)
        if scheme:
            return scheme, uses_crypto

    direct_buttons = app.get('buttons', [])
    if direct_buttons:
        scheme, uses_crypto = _extract_scheme_from_buttons(direct_buttons)
        if scheme:
            return scheme, uses_crypto

    logger.debug(
        '_get_url_scheme_for_app: No scheme found for app has blocks: has buttons: has urlScheme',
        get=app.get('name'),
        get_2=bool(app.get('blocks')),
        get_3=bool(app.get('buttons')),
        get_4=bool(app.get('urlScheme')),
    )
    return '', False


async def _load_app_config_async() -> dict[str, Any] | None:
    """Load app config from RemnaWave API (if configured)."""
    remnawave_uuid = _get_remnawave_config_uuid()

    if remnawave_uuid:
        try:
            service = RemnaWaveService()
            async with service.get_api_client() as api:
                config = await api.get_subscription_page_config(remnawave_uuid)
                if config and config.config:
                    logger.debug('Loaded app config from RemnaWave', remnawave_uuid=remnawave_uuid)
                    raw = dict(config.config)
                    raw['_isRemnawave'] = True
                    return raw
        except Exception as e:
            logger.warning('Failed to load RemnaWave config', error=e)

    return None


def _create_deep_link(
    app: dict[str, Any], subscription_url: str | None, subscription_crypto_link: str | None = None
) -> str | None:
    """Create deep link for app with subscription URL."""
    if not isinstance(app, dict):
        return None

    if not subscription_url and not subscription_crypto_link:
        return None

    scheme, uses_crypto = _get_url_scheme_for_app(app)
    if not scheme:
        logger.debug('_create_deep_link: no urlScheme for app', get=app.get('name', 'unknown'))
        return None

    if uses_crypto:
        if not subscription_crypto_link:
            logger.debug(
                '_create_deep_link: app requires crypto link but none available', get=app.get('name', 'unknown')
            )
            return None
        payload = subscription_crypto_link
    else:
        if not subscription_url:
            logger.debug(
                '_create_deep_link: app requires subscription_url but none available', get=app.get('name', 'unknown')
            )
            return None
        payload = subscription_url

    if app.get('isNeedBase64Encoding'):
        try:
            payload = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.warning('Failed to encode payload to base64', error=e)

    return f'{scheme}{payload}'


def _resolve_button_url(
    url: str,
    subscription_url: str | None,
    subscription_crypto_link: str | None,
) -> str:
    """Resolve template variables in button URLs."""
    if not url:
        return url
    result = url
    if subscription_url:
        result = result.replace('{{SUBSCRIPTION_LINK}}', subscription_url)
    if subscription_crypto_link:
        result = result.replace('{{HAPP_CRYPT3_LINK}}', subscription_crypto_link)
        result = result.replace('{{HAPP_CRYPT4_LINK}}', subscription_crypto_link)
    return result
