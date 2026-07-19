"""Helper functions for subscription app-config/deep-link rendering."""

import base64
import json
import os
import re
from typing import Any

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings
from app.services.remnawave_service import RemnaWaveService
from app.services.system_settings_service import bot_configuration_service


logger = structlog.get_logger(__name__)

_INCY_CRYPT1_PREFIX = 'incy://crypt1/'
_HAPP_CRYPT5_PREFIX = 'happ://crypt5/'
# Public compatibility key from @incy/link-encoder. crypt1 is obfuscation,
# not secret storage; INCY clients ship the same key.
_INCY_CRYPT1_KEY = bytes.fromhex('f6d40ea0c8a8899d7c682d09ba0d4165dfe2b3dd45e6bb3e25cb233cf00c2462')


def _is_app(app: dict[str, Any], app_id: str) -> bool:
    identity = ' '.join(str(app.get(field, '')).strip().lower() for field in ('id', 'name', 'urlScheme'))
    return app_id in identity


def _select_synced_happ_link(
    current_link: str | None,
    panel_link: str | None,
    *,
    subscription_url_changed: bool,
) -> str | None:
    """Keep a local crypt5 link unless the source subscription URL changed."""
    if str(panel_link or '').startswith(_HAPP_CRYPT5_PREFIX):
        return panel_link
    if subscription_url_changed:
        return panel_link
    if str(current_link or '').startswith(_HAPP_CRYPT5_PREFIX):
        return current_link
    return panel_link or current_link


def _create_incy_crypto_link(subscription_url: str | None, provider_name: str | None = None) -> str | None:
    """Build the public INCY crypt1 wire format without an external request."""
    if not subscription_url or not subscription_url.lower().startswith(('http://', 'https://')):
        return None

    payload: dict[str, Any] = {'url': subscription_url, 'v': 1}
    if provider_name:
        payload['n'] = provider_name[:128]

    plaintext = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(',', ':'),
        sort_keys=True,
    ).encode('utf-8')
    iv = os.urandom(12)
    encrypted = AESGCM(_INCY_CRYPT1_KEY).encrypt(iv, plaintext, None)
    encoded = base64.urlsafe_b64encode(iv + encrypted).decode('ascii').rstrip('=')
    return f'{_INCY_CRYPT1_PREFIX}{encoded}'


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
        uses_crypto_link=True when the template is a Happ crypto link,
        meaning subscription_crypto_link should be used as payload.
    """
    for btn in buttons:
        if not isinstance(btn, dict):
            continue
        link = btn.get('link', '') or btn.get('url', '') or btn.get('buttonLink', '')
        if not link:
            continue
        link_upper = link.upper()

        if re.search(r'HAPP_CRYPT[345]_LINK', link_upper):
            scheme = re.sub(r'\{\{HAPP_CRYPT[345]_LINK\}\}', '', link, flags=re.IGNORECASE)
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
    app: dict[str, Any],
    subscription_url: str | None,
    subscription_crypto_link: str | None = None,
    subscription_incy_crypto_link: str | None = None,
) -> str | None:
    """Create deep link for app with subscription URL."""
    if not isinstance(app, dict):
        return None

    if not subscription_url and not subscription_crypto_link and not subscription_incy_crypto_link:
        return None

    if _is_app(app, 'incy') and subscription_incy_crypto_link:
        return subscription_incy_crypto_link

    if _is_app(app, 'happ') and subscription_crypto_link:
        return subscription_crypto_link

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

    scheme_prefix = scheme if '://' in scheme else f'{scheme}://'
    return f'{scheme_prefix}{payload}'


def _resolve_button_url(
    url: str,
    subscription_url: str | None,
    subscription_crypto_link: str | None,
    subscription_incy_crypto_link: str | None = None,
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
        result = result.replace('{{HAPP_CRYPT5_LINK}}', subscription_crypto_link)
    if subscription_incy_crypto_link:
        result = result.replace('{{INCY_CRYPT1_LINK}}', subscription_incy_crypto_link)
    return result
