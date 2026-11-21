import hashlib
import hmac
import json
import sys
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cabinet.routes import antarctic
from app.database.models import Tariff


@pytest.mark.asyncio
async def test_offer_uses_existing_tariff_monthly_price_and_limits(monkeypatch):
    squad = str(uuid4())
    external_squad = str(uuid4())
    tariff = Tariff(
        name='Working tariff',
        period_prices={'30': 42500, '90': 100000},
        device_limit=3,
        traffic_limit_gb=12,
        allowed_squads=[squad],
        external_squad_uuid=external_squad,
        traffic_reset_mode='NO_RESET',
    )
    db = SimpleNamespace(scalars=AsyncMock(return_value=[tariff]))
    monkeypatch.setattr(antarctic.currency_converter, 'get_usd_to_rub_rate', AsyncMock(return_value=85))

    offer = await antarctic._offer(db)

    assert offer['plan_name'] == tariff.name
    assert offer['amount'] == '5.00'
    assert offer['days'] == 30
    assert offer['device_limit'] == 3
    assert offer['plan_config'] == {
        'squads': [squad],
        'external_squad': external_squad,
        'traffic_bytes': 12 * 1024**3,
        'traffic_strategy': 'NO_RESET',
    }


@pytest.mark.asyncio
async def test_monthly_checkout_validates_payment_and_issues_subscription_once(monkeypatch):
    app = FastAPI()
    app.include_router(antarctic.router)
    owner = 'test-app:0123456789abcdef'
    actor = [owner]
    operation = str(uuid4())
    internal_squad = str(uuid4())
    secret = 'test-secret'
    # The default test bootstrap stubs this driver. This test uses real SQLite.
    if not hasattr(sys.modules.get('aiosqlite'), 'Connection'):
        monkeypatch.delitem(sys.modules, 'aiosqlite', raising=False)
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def db_override():
        async with sessions() as db:
            yield db

    app.dependency_overrides[antarctic.get_cabinet_db] = db_override
    app.dependency_overrides[antarctic._owner] = lambda: actor[0]
    monkeypatch.setattr(antarctic, '_wallet_config', dict)
    monkeypatch.setattr(antarctic.settings, 'ANTARCTIC_APP_ID', 'test-app')
    monkeypatch.setattr(antarctic.settings, 'ANTARCTIC_APP_SECRET', secret)
    offer = {
        'amount': '4.25',
        'plan_name': 'Monthly',
        'days': 30,
        'device_limit': 3,
        'plan_config': {
            'squads': [internal_squad],
            'external_squad': None,
            'traffic_bytes': 10 * 1024**3,
            'traffic_strategy': 'NO_RESET',
        },
    }
    monkeypatch.setattr(antarctic, '_offer', AsyncMock(return_value=offer))
    intent = AsyncMock(return_value={'operation_id': operation, 'status': 'pending'})
    monkeypatch.setattr(antarctic, '_intent', intent)
    panel = SimpleNamespace(
        get_user_by_username=AsyncMock(return_value=None),
        create_user=AsyncMock(return_value=SimpleNamespace(subscription_url='https://sub.example/vpn')),
    )

    @asynccontextmanager
    async def panel_client():
        yield panel

    monkeypatch.setattr(antarctic, 'SubscriptionService', lambda: SimpleNamespace(get_api_client=panel_client))

    def migrate(connection):
        migration = import_module('migrations.alembic.versions.0061_add_antarctic_orders')
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

    try:
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            created = await client.post('/antarctic/checkout')
            assert created.status_code == 200
            assert created.json()['operation_id'] == operation
            assert (await client.post('/antarctic/checkout')).json() == created.json()
            intent.assert_awaited_once()
            request = intent.await_args.kwargs['json']
            assert request['data']['amount'] == '4.25'

            async def webhook(amount, signed=True):
                data = {
                    'event': 'intent.approved',
                    'data': {
                        'type': 'pay',
                        'status': 'approved',
                        'operation_id': operation,
                        'reference_id': request['reference_id'],
                        'user_app_login': owner.split(':')[1],
                        'approved_at': datetime.now(UTC).isoformat(),
                        'data': {'amount': amount},
                    },
                }
                raw = json.dumps(data).encode()
                timestamp = str(int(time.time()))
                signature = hmac.digest(
                    secret.encode(), f'{timestamp}.{hashlib.sha256(raw).hexdigest()}'.encode(), 'sha256'
                )
                return await client.post(
                    '/antarctic/webhook',
                    content=raw,
                    headers={
                        'X-Sdk-Webhook-Timestamp': timestamp,
                        'X-Sdk-Webhook-Signature': signature.hex() if signed else '',
                    },
                )

            assert (await webhook('4.25', signed=False)).status_code == 401
            assert (await webhook('1.00')).status_code == 409
            panel.create_user.assert_not_awaited()
            assert (await webhook('4.25')).status_code == 204
            assert (await webhook('4.25')).status_code == 204
            panel.create_user.assert_awaited_once()
            assert panel.create_user.await_args.kwargs['active_internal_squads'] == [internal_squad]
            assert panel.create_user.await_args.kwargs['traffic_limit_bytes'] == 10 * 1024**3
            status = await client.post('/antarctic/status')
            assert status.json()['subscription_url'] == 'https://sub.example/vpn'
            actor[0] = 'test-app:1111111111111111'
            assert (await client.post('/antarctic/status')).json() is None
    finally:
        await engine.dispose()
