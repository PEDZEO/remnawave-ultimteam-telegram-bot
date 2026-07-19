import base64
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.cabinet.routes.subscription_app_config_helpers import (
    _INCY_CRYPT1_KEY,
    _create_deep_link,
    _create_incy_crypto_link,
    _resolve_button_url,
    _select_synced_happ_link,
)


def test_incy_crypt1_link_contains_subscription_and_provider() -> None:
    link = _create_incy_crypto_link('https://sub.example/token', 'Ultimteam VPN')

    assert link is not None
    assert link.startswith('incy://crypt1/')
    encoded = link.removeprefix('incy://crypt1/')
    wire = base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4))
    plaintext = AESGCM(_INCY_CRYPT1_KEY).decrypt(wire[:12], wire[12:], None)

    assert json.loads(plaintext) == {
        'n': 'Ultimteam VPN',
        'url': 'https://sub.example/token',
        'v': 1,
    }


def test_incy_crypto_key_decodes_official_crypt1_example() -> None:
    encoded = 'FZEVXuV39UEX1yHB3nkrgdPdrJ3syVxcQm_Y-lY0oKWAT5yRn00xe6ohg06aVWjWRrGJ7BAeEzuoFzv8XBosLnqnqqCMbnAJmR7EN2hII4Yyql1FtWlLlLs'
    wire = base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4))

    plaintext = AESGCM(_INCY_CRYPT1_KEY).decrypt(wire[:12], wire[12:], None)

    assert json.loads(plaintext) == {
        'url': 'https://incsub.myincteam.org/vTyt0xVE-aAjHv8T',
        'v': 1,
    }


def test_panel_sync_does_not_downgrade_crypt5_until_subscription_url_changes() -> None:
    current = 'happ://crypt5/current'
    old_panel_link = 'happ://crypt4/panel'

    assert _select_synced_happ_link(current, old_panel_link, subscription_url_changed=False) == current
    assert _select_synced_happ_link(current, old_panel_link, subscription_url_changed=True) == old_panel_link
    assert (
        _select_synced_happ_link(current, 'happ://crypt5/panel', subscription_url_changed=False)
        == 'happ://crypt5/panel'
    )


def test_client_specific_deep_links_are_not_wrapped_in_redirects() -> None:
    happ_link = 'happ://crypt5/payload'
    incy_link = 'incy://crypt1/payload'

    assert (
        _create_deep_link(
            {'id': 'happ', 'name': 'Happ', 'urlScheme': 'happ://add/'},
            'https://sub.example/token',
            happ_link,
            incy_link,
        )
        == happ_link
    )
    assert (
        _create_deep_link(
            {'id': 'incy', 'name': 'INCY', 'urlScheme': 'incy://add/'},
            'https://sub.example/token',
            happ_link,
            incy_link,
        )
        == incy_link
    )
    assert (
        _create_deep_link(
            {'id': 'stash', 'name': 'Stash', 'urlScheme': 'stash://install-config?url='},
            'https://sub.example/token',
            happ_link,
            incy_link,
        )
        == 'stash://install-config?url=https://sub.example/token'
    )
    assert (
        _create_deep_link(
            {'id': 'v2box', 'name': 'V2Box', 'urlScheme': 'v2box'},
            'https://sub.example/token',
        )
        == 'v2box://https://sub.example/token'
    )


def test_new_crypto_templates_are_resolved() -> None:
    assert (
        _resolve_button_url(
            '{{HAPP_CRYPT5_LINK}}',
            'https://sub.example/token',
            'happ://crypt5/payload',
            'incy://crypt1/payload',
        )
        == 'happ://crypt5/payload'
    )
    assert (
        _resolve_button_url(
            '{{INCY_CRYPT1_LINK}}',
            'https://sub.example/token',
            'happ://crypt5/payload',
            'incy://crypt1/payload',
        )
        == 'incy://crypt1/payload'
    )
