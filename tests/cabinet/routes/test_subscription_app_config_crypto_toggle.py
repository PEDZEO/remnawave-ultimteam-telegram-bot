from types import SimpleNamespace
from typing import Any

import pytest

from app.cabinet.routes import subscription as subscription_routes


class FakeDb:
    async def refresh(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def commit(self) -> None:
        return None


async def _noop_refresh(*args: Any, **kwargs: Any) -> None:
    return None


async def _minimal_app_config() -> dict[str, Any]:
    return {
        'brandingSettings': {'name': 'Ultimteam VPN'},
        'platforms': {
            'android': {
                'apps': [
                    {'id': 'happ', 'name': 'Happ', 'urlScheme': 'happ://add/', 'blocks': []},
                    {'id': 'incy', 'name': 'INCY', 'urlScheme': 'incy://add/', 'blocks': []},
                ]
            }
        },
    }


@pytest.mark.asyncio
async def test_app_config_hides_crypto_payloads_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subscription_routes.settings, 'CABINET_CRYPTO_LINKS_ENABLED', False)
    monkeypatch.setattr(subscription_routes, '_refresh_subscription_link_from_panel', _noop_refresh)
    monkeypatch.setattr(subscription_routes, '_load_app_config_async', _minimal_app_config)
    user = SimpleNamespace(
        id=12,
        subscription=SimpleNamespace(
            subscription_url='https://sub.example/token',
            subscription_crypto_link='happ://crypt5/stored-payload',
        ),
    )

    response = await subscription_routes.get_app_config(user=user, db=FakeDb())

    assert response['hasSubscription'] is True
    assert response['cryptoLinksEnabled'] is False
    assert response['subscriptionCryptoLink'] is None
    assert response['subscriptionIncyCryptoLink'] is None
    assert [app['deepLink'] for app in response['platforms']['android']['apps']] == [
        'https://sub.example/token',
        'https://sub.example/token',
    ]


@pytest.mark.asyncio
async def test_app_config_exposes_saved_crypto_payloads_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subscription_routes.settings, 'CABINET_CRYPTO_LINKS_ENABLED', True)
    monkeypatch.setattr(subscription_routes, '_refresh_subscription_link_from_panel', _noop_refresh)
    monkeypatch.setattr(subscription_routes, '_load_app_config_async', _minimal_app_config)
    user = SimpleNamespace(
        id=12,
        subscription=SimpleNamespace(
            subscription_url='https://sub.example/token',
            subscription_crypto_link='happ://crypt5/stored-payload',
        ),
    )

    response = await subscription_routes.get_app_config(user=user, db=FakeDb())

    assert response['cryptoLinksEnabled'] is True
    assert response['subscriptionCryptoLink'] == 'happ://crypt5/stored-payload'
    assert response['subscriptionIncyCryptoLink'].startswith('incy://crypt1/')
    assert response['platforms']['android']['apps'][0]['deepLink'] == 'happ://crypt5/stored-payload'
    assert response['platforms']['android']['apps'][1]['deepLink'].startswith('incy://crypt1/')


@pytest.mark.asyncio
async def test_legacy_connection_endpoint_cannot_leak_crypto_link_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subscription_routes.settings, 'CABINET_CRYPTO_LINKS_ENABLED', False)
    monkeypatch.setattr(subscription_routes.settings, 'CONNECT_BUTTON_MODE', 'happ_cryptolink')
    monkeypatch.setattr(subscription_routes, '_refresh_subscription_link_from_panel', _noop_refresh)
    user = SimpleNamespace(
        subscription=SimpleNamespace(
            subscription_url='https://sub.example/token',
            subscription_crypto_link='happ://crypt5/stored-payload',
        )
    )

    response = await subscription_routes.get_connection_link(user=user, db=FakeDb())

    assert response['connect_mode'] == 'url'
    assert response['subscription_url'] == 'https://sub.example/token'
    assert response['display_link'] == 'https://sub.example/token'
    assert response['happ_redirect_link'] is None
    assert response['happ_scheme_link'] is None
