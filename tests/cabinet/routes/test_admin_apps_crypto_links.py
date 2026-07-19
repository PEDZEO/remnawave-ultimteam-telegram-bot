from types import SimpleNamespace
from typing import Any

import pytest

from app.cabinet.routes import admin_apps
from app.cabinet.routes.admin_apps import CryptoLinksSettings


class FakeDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_crypto_links_settings_returns_live_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        admin_apps.bot_configuration_service,
        'get_current_value',
        lambda key: key == 'CABINET_CRYPTO_LINKS_ENABLED',
    )

    response = await admin_apps.get_crypto_links_settings(admin=SimpleNamespace(id=1))

    assert response == CryptoLinksSettings(enabled=True)


@pytest.mark.asyncio
async def test_crypto_links_settings_updates_database_override(monkeypatch: pytest.MonkeyPatch) -> None:
    saved: list[tuple[str, Any]] = []

    async def set_value(db: Any, key: str, value: Any) -> None:
        saved.append((key, value))

    monkeypatch.setattr(admin_apps.bot_configuration_service, 'set_value', set_value)
    db = FakeDb()

    response = await admin_apps.update_crypto_links_settings(
        request=CryptoLinksSettings(enabled=False),
        admin=SimpleNamespace(id=7),
        db=db,
    )

    assert response == CryptoLinksSettings(enabled=False)
    assert saved == [('CABINET_CRYPTO_LINKS_ENABLED', False)]
    assert db.commits == 1
    assert db.rollbacks == 0
