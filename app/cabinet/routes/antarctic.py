"""Fixed-price Antarctic Wallet checkout and RemnaWave delivery."""

import hashlib
import hmac
import json
import re
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import AntarcticOrder, Tariff
from app.external.remnawave_api import RemnaWaveAPIError, TrafficLimitStrategy
from app.services.subscription_service import SubscriptionService, get_traffic_reset_strategy
from app.utils.currency_converter import currency_converter

from ..dependencies import get_cabinet_db


router = APIRouter(prefix='/antarctic', tags=['Antarctic Wallet'])
INTENTS = '/api/apps/v1/intents'
PLAN_DAYS = 30


def _https_origin(value: str) -> bool:
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return bool(
        parts.scheme == 'https' and parts.hostname and value == f'https://{parts.netloc}' and not parts.username
    )


def _wallet_config() -> dict:
    origins = settings.ANTARCTIC_WALLET_ORIGINS.split()
    if not (
        re.fullmatch(r'[A-Za-z0-9_-]{1,40}', settings.ANTARCTIC_APP_ID)
        and settings.ANTARCTIC_APP_SECRET
        and _https_origin(settings.ANTARCTIC_API_BASE)
        and origins
        and all(map(_https_origin, origins))
        and settings.REMNAWAVE_API_URL
        and settings.REMNAWAVE_API_KEY
    ):
        raise HTTPException(503, 'Antarctic checkout is unavailable')
    return {
        'app_id': settings.ANTARCTIC_APP_ID,
        'origins': origins,
    }


async def _offer(db: AsyncSession) -> dict:
    query = select(Tariff).where(Tariff.is_active.is_(True), Tariff.is_daily.is_(False))
    if settings.ANTARCTIC_TARIFF_ID is not None:
        query = query.where(Tariff.id == settings.ANTARCTIC_TARIFF_ID)
    tariffs = [tariff for tariff in await db.scalars(query) if (tariff.get_price_for_period(PLAN_DAYS) or 0) > 0]
    if len(tariffs) != 1:
        raise HTTPException(503, 'Select one active monthly tariff for Antarctic')
    tariff = tariffs[0]
    if not tariff.allowed_squads or tariff.server_traffic_limits or tariff.special_servers_enabled:
        raise HTTPException(503, 'Monthly tariff requires compatible RemnaWave limits')
    rate = Decimal(str(await currency_converter.get_usd_to_rub_rate()))
    if not rate.is_finite() or rate <= 0:
        raise HTTPException(503, 'Currency conversion is unavailable')
    price = (Decimal(tariff.get_price_for_period(PLAN_DAYS)) / (rate * 100)).quantize(Decimal('0.01'))
    if price <= 0:
        raise HTTPException(503, 'Invalid monthly tariff price')
    return {
        'amount': str(price),
        'plan_name': tariff.name,
        'days': PLAN_DAYS,
        'device_limit': tariff.device_limit,
        'plan_config': {
            'squads': tariff.allowed_squads,
            'external_squad': tariff.external_squad_uuid,
            'traffic_bytes': tariff.traffic_limit_gb * 1024**3,
            'traffic_strategy': get_traffic_reset_strategy(tariff).value,
        },
    }


async def _owner(authorization: str = Header(default='')) -> str:
    _wallet_config()
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token or len(token) > 8192:
        raise HTTPException(401, 'Wallet authorization required')
    try:
        header = jwt.get_unverified_header(token)
        if header.get('alg') not in ('RS256', 'ES256', 'EdDSA') or not header.get('kid'):
            raise jwt.InvalidTokenError
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(f'{settings.ANTARCTIC_API_BASE}/api/v2/sdk/jwks')
            response.raise_for_status()
        key = next(jwk for jwk in response.json()['keys'] if jwk.get('kid') == header['kid'])
        signing_key = jwt.PyJWK.from_dict(key)
        if signing_key.algorithm_name != header['alg']:
            raise jwt.InvalidTokenError
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=[header['alg']],
            issuer='aw',
            audience=settings.ANTARCTIC_APP_ID,
            options={'require': ['exp', 'iss', 'aud', 'sub']},
        )
        if not re.fullmatch(r'[0-9a-f]{16}', claims['sub']):
            raise jwt.InvalidTokenError
    except httpx.HTTPError as exc:
        raise HTTPException(502, 'Wallet authorization unavailable') from exc
    except (jwt.PyJWTError, ValueError, KeyError, TypeError, StopIteration) as exc:
        raise HTTPException(401, 'Invalid wallet session') from exc
    return f'{settings.ANTARCTIC_APP_ID}:{claims["sub"]}'


async def _intent(method: str, suffix: str = '', **kwargs) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(
                method,
                f'{settings.ANTARCTIC_API_BASE}{INTENTS}{suffix}',
                headers={
                    'X-AW-App-Id': settings.ANTARCTIC_APP_ID,
                    'Authorization': f'Bearer {settings.ANTARCTIC_APP_SECRET}',
                },
                **kwargs,
            )
        if method == 'POST' and response.status_code == 409:
            return await _intent('GET', f'/{kwargs["json"]["reference_id"]}')
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError
        nested = payload.get('data')
        return nested if isinstance(nested, dict) and ('operation_id' in nested or 'operationId' in nested) else payload
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, 'Wallet payment service unavailable') from exc


def _order_response(order: AntarcticOrder | None) -> dict | None:
    if order is None:
        return None
    return {
        'status': order.status,
        'operation_id': order.operation_id,
        'subscription_url': order.subscription_url,
        'expires_at': order.expires_at,
        'amount': order.amount,
        'plan_name': order.plan_name,
        'days': order.days,
        'device_limit': order.device_limit,
    }


async def _latest(db: AsyncSession, owner: str) -> AntarcticOrder | None:
    return await db.scalar(
        select(AntarcticOrder)
        .where(AntarcticOrder.owner == owner)
        .order_by(AntarcticOrder.created_at.desc(), AntarcticOrder.id.desc())
        .limit(1)
    )


def _closed(order: AntarcticOrder) -> bool:
    return order.status in ('rejected', 'expired', 'failed') or (
        order.status == 'delivered' and order.expires_at <= datetime.now(UTC)
    )


async def _deliver(db: AsyncSession, order: AntarcticOrder) -> None:
    if order.status != 'paid':
        return
    username = 'aw_' + UUID(order.id).hex[:24]
    try:
        async with SubscriptionService().get_api_client() as api:
            user = await api.get_user_by_username(username)
            if user is None:
                user = await api.create_user(
                    username=username,
                    expire_at=order.expires_at,
                    hwid_device_limit=order.device_limit,
                    active_internal_squads=order.plan_config['squads'],
                    external_squad_uuid=order.plan_config['external_squad'],
                    traffic_limit_bytes=order.plan_config['traffic_bytes'],
                    traffic_limit_strategy=TrafficLimitStrategy(order.plan_config['traffic_strategy']),
                    enforce_native_traffic_limit=True,
                    description=f'Antarctic Wallet order {order.id}',
                )
    except (RemnaWaveAPIError, httpx.HTTPError) as exc:
        raise HTTPException(503, 'Subscription delivery will be retried') from exc
    subscription = urlsplit(user.subscription_url or '')
    if not subscription.hostname or subscription.scheme != 'https':
        raise HTTPException(503, 'RemnaWave subscription URL is unavailable')
    order.subscription_url = user.subscription_url
    order.status = 'delivered'
    await db.commit()


def _matches_payment(order: AntarcticOrder, data: dict) -> bool:
    try:
        return (
            data['type'] == 'pay'
            and data['reference_id'] == order.id
            and data['user_app_login'] == order.owner.split(':', 1)[1]
            and Decimal(str(data['data']['amount'])) == Decimal(order.amount)
        )
    except (KeyError, TypeError, InvalidOperation):
        return False


async def _settle(db: AsyncSession, order: AntarcticOrder, data: dict) -> None:
    state = data.get('status')
    try:
        operation_id = str(UUID(data.get('operation_id') or data.get('operationId')))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(409, 'Invalid payment operation') from None
    if not _matches_payment(order, data) or order.operation_id not in (None, operation_id):
        raise HTTPException(409, 'Payment does not match order')
    if state == 'approved':
        try:
            approved_at = datetime.fromisoformat(data['approved_at'])
            if approved_at.utcoffset() is None:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise HTTPException(409, 'Invalid approval time') from None
        changes = {'status': 'paid', 'expires_at': approved_at.astimezone(UTC) + timedelta(days=order.days)}
    elif state in ('rejected', 'expired', 'failed'):
        changes = {'status': state}
    else:
        return
    await db.execute(
        update(AntarcticOrder)
        .where(
            AntarcticOrder.id == order.id,
            AntarcticOrder.status == 'pending',
        )
        .values(operation_id=operation_id, **changes)
    )
    await db.commit()
    await db.refresh(order)
    await _deliver(db, order)


@router.get('/config')
async def checkout_config(response: Response, db: AsyncSession = Depends(get_cabinet_db)) -> dict:
    response.headers['Cache-Control'] = 'no-store'
    return _wallet_config() | {key: value for key, value in (await _offer(db)).items() if key != 'plan_config'}


@router.post('/status')
async def checkout_status(
    response: Response,
    owner: str = Depends(_owner),
    db: AsyncSession = Depends(get_cabinet_db),
) -> dict | None:
    response.headers['Cache-Control'] = 'no-store'
    order = await _latest(db, owner)
    if order and order.status == 'pending' and order.operation_id:
        data = await _intent('GET', f'/{order.operation_id}')
        if data.get('status') in ('approved', 'rejected', 'expired', 'failed'):
            await _settle(db, order, data)
    if order and order.status == 'paid':
        await _deliver(db, order)
    return _order_response(order)


@router.post('/checkout')
async def checkout(
    response: Response,
    owner: str = Depends(_owner),
    db: AsyncSession = Depends(get_cabinet_db),
) -> dict:
    response.headers['Cache-Control'] = 'no-store'
    order = await _latest(db, owner)
    if order is None or _closed(order):
        reference = str(uuid5(NAMESPACE_URL, f'antarctic:{owner}:{order.id if order else "first"}'))
        order = AntarcticOrder(
            id=reference,
            owner=owner,
            status='pending',
            created_at=datetime.now(UTC),
            **await _offer(db),
        )
        db.add(order)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            order = await db.get(AntarcticOrder, reference)
            if order is None:
                raise

    if order.status == 'pending' and not order.operation_id:
        data = await _intent(
            'POST',
            json={
                'type': 'pay',
                'user_app_login': owner.split(':', 1)[1],
                'reference_id': order.id,
                'data': {'amount': order.amount},
            },
        )
        try:
            operation_id = str(UUID(data.get('operationId') or data.get('operation_id')))
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(502, 'Wallet did not return a payment operation') from None
        await db.execute(
            update(AntarcticOrder)
            .where(
                AntarcticOrder.id == order.id,
                AntarcticOrder.operation_id.is_(None),
            )
            .values(operation_id=operation_id)
        )
        await db.commit()
        await db.refresh(order)
    return _order_response(order)


def _valid_signature(raw: bytes, timestamp: str, signature: str, secret: str) -> bool:
    if not re.fullmatch(r'[0-9]{1,12}', timestamp) or abs(time.time() - int(timestamp)) > 300:
        return False
    message = f'{timestamp}.{hashlib.sha256(raw).hexdigest()}'.encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return bool(re.fullmatch(r'[a-f0-9]{64}', signature) and hmac.compare_digest(expected, signature))


@router.post('/webhook', status_code=204)
async def wallet_webhook(request: Request, db: AsyncSession = Depends(get_cabinet_db)) -> Response:
    _wallet_config()
    raw = await request.body()
    if not _valid_signature(
        raw,
        request.headers.get('X-Sdk-Webhook-Timestamp', ''),
        request.headers.get('X-Sdk-Webhook-Signature', ''),
        settings.ANTARCTIC_APP_SECRET,
    ):
        raise HTTPException(401, 'Invalid wallet webhook signature')
    try:
        payload = json.loads(raw)
        expected_status = {'intent.approved': 'approved', 'intent.rejected': 'rejected'}.get(payload['event'])
        if expected_status is None:
            return Response(status_code=204)
        data = payload['data']
        if data['status'] != expected_status:
            raise ValueError
        order_id = str(UUID(data['reference_id']))
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise HTTPException(400, 'Invalid wallet event') from exc
    order = await db.get(AntarcticOrder, order_id)
    if order is not None and order.owner.startswith(f'{settings.ANTARCTIC_APP_ID}:'):
        await _settle(db, order, data)
    return Response(status_code=204)
