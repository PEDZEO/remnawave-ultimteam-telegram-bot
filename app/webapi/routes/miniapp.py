from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.discount_offer import (
    get_latest_claimed_offer_for_user,
    get_offer_by_id,
    list_active_discount_offers_for_user,
    mark_offer_claimed,
)
from app.database.crud.promo_group import get_auto_assign_promo_groups
from app.database.crud.promo_offer_template import get_promo_offer_template_by_id
from app.database.crud.rules import get_rules_by_language
from app.database.crud.subscription import (
    create_trial_subscription,
    extend_subscription,
    update_subscription_autopay,
)
from app.database.crud.transaction import (
    create_transaction,
    get_user_total_spent_kopeks,
)
from app.database.crud.user import get_user_by_telegram_id, subtract_user_balance
from app.database.models import (
    Transaction,
    TransactionType,
)
from app.services.faq_service import FaqService
from app.services.maintenance_service import maintenance_service
from app.services.payment_service import PaymentService, get_wata_payment_by_link_id
from app.services.privacy_policy_service import PrivacyPolicyService
from app.services.promo_offer_service import promo_offer_service
from app.services.promocode_service import PromoCodeService
from app.services.public_offer_service import PublicOfferService
from app.services.remnawave_service import (
    RemnaWaveConfigurationError,
    RemnaWaveService,
)
from app.services.subscription_purchase_service import (
    PurchaseBalanceError,
    PurchaseValidationError,
    purchase_service,
)
from app.services.subscription_renewal_service import (
    SubscriptionRenewalService,
    calculate_missing_amount,
    with_admin_notification_service,
)
from app.services.subscription_service import SubscriptionService
from app.services.trial_activation_service import (
    TrialPaymentChargeFailed,
    TrialPaymentInsufficientFunds,
    charge_trial_activation_if_required,
    preview_trial_activation_charge,
    revert_trial_activation,
    rollback_trial_subscription_activation,
)
from app.services.trial_parameters_service import resolve_trial_parameters
from app.services.tribute_service import TributeService
from app.utils.subscription_utils import get_happ_cryptolink_redirect_link
from app.utils.telegram_webapp import (
    TelegramWebAppAuthError,
    parse_webapp_init_data,
)

from ..dependencies import get_db_session
from ..schemas.miniapp import (
    MiniAppAutoPromoGroupLevel,
    MiniAppConnectedServer,
    MiniAppDailySubscriptionToggleRequest,
    MiniAppDailySubscriptionToggleResponse,
    MiniAppDeviceRemovalRequest,
    MiniAppDeviceRemovalResponse,
    MiniAppFaq,
    MiniAppFaqItem,
    MiniAppLegalDocuments,
    MiniAppMaintenanceStatusResponse,
    MiniAppPaymentCreateRequest,
    MiniAppPaymentCreateResponse,
    MiniAppPaymentIntegrationType,
    MiniAppPaymentMethod,
    MiniAppPaymentMethodsRequest,
    MiniAppPaymentMethodsResponse,
    MiniAppPaymentOption,
    MiniAppPaymentStatusRequest,
    MiniAppPaymentStatusResponse,
    MiniAppPaymentStatusResult,
    MiniAppPromoCode,
    MiniAppPromoCodeActivationRequest,
    MiniAppPromoCodeActivationResponse,
    MiniAppPromoGroup,
    MiniAppPromoOfferClaimRequest,
    MiniAppPromoOfferClaimResponse,
    MiniAppRichTextDocument,
    MiniAppSubscriptionAutopayRequest,
    MiniAppSubscriptionAutopayResponse,
    MiniAppSubscriptionDevicesUpdateRequest,
    MiniAppSubscriptionPurchaseOptionsRequest,
    MiniAppSubscriptionPurchaseOptionsResponse,
    MiniAppSubscriptionPurchasePreviewRequest,
    MiniAppSubscriptionPurchasePreviewResponse,
    MiniAppSubscriptionPurchaseRequest,
    MiniAppSubscriptionPurchaseResponse,
    MiniAppSubscriptionRenewalOptionsRequest,
    MiniAppSubscriptionRenewalOptionsResponse,
    MiniAppSubscriptionRenewalRequest,
    MiniAppSubscriptionRenewalResponse,
    MiniAppSubscriptionRequest,
    MiniAppSubscriptionResponse,
    MiniAppSubscriptionServersUpdateRequest,
    MiniAppSubscriptionSettingsRequest,
    MiniAppSubscriptionSettingsResponse,
    MiniAppSubscriptionTrafficUpdateRequest,
    MiniAppSubscriptionTrialRequest,
    MiniAppSubscriptionTrialResponse,
    MiniAppSubscriptionUpdateResponse,
    MiniAppSubscriptionUser,
    MiniAppTariffPurchaseRequest,
    MiniAppTariffPurchaseResponse,
    MiniAppTariffsRequest,
    MiniAppTariffsResponse,
    MiniAppTariffSwitchPreviewResponse,
    MiniAppTariffSwitchRequest,
    MiniAppTariffSwitchResponse,
    MiniAppTrafficTopupRequest,
    MiniAppTrafficTopupResponse,
)
from .miniapp_auth_helpers import (
    authorize_miniapp_user as _authorize_miniapp_user_impl,
    ensure_paid_subscription as _ensure_paid_subscription_impl,
)
from .miniapp_autopay_helpers import (
    _autopay_response_extras,
    _build_autopay_payload,
    _get_autopay_day_options,
    _normalize_autopay_days,
)
from .miniapp_cryptobot_helpers import (
    compute_cryptobot_limits as _compute_cryptobot_limits_impl,
    get_usd_to_rub_rate as _get_usd_to_rub_rate_impl,
)
from .miniapp_format_helpers import (
    bytes_to_gb,
    format_gb,
    format_gb_label,
    format_limit_label,
    status_label,
)
from .miniapp_helpers.auth_runtime import resolve_user_from_init_data as _resolve_user_from_init_data_impl
from .miniapp_helpers.payment.amount import (
    build_balance_invoice_payload,
    compute_stars_min_amount,
    current_request_timestamp,
    normalize_stars_amount,
)
from .miniapp_helpers.payment.create_cryptobot import (
    create_cryptobot_balance_payment_response,
)
from .miniapp_helpers.payment.create_input import (
    resolve_create_payment_amount,
    resolve_create_payment_method,
)
from .miniapp_helpers.payment.create_yookassa import (
    create_yookassa_balance_payment_response,
    create_yookassa_sbp_balance_payment_response,
)
from .miniapp_helpers.payment.lookup import find_recent_deposit as _find_recent_deposit_impl
from .miniapp_helpers.payment.request import (
    build_mulenpay_iframe_config,
)
from .miniapp_helpers.payment_status.base import (
    resolve_yookassa_payment_status as _resolve_yookassa_payment_status_impl,
)
from .miniapp_helpers.payment_status.common import (
    classify_payment_status,
)
from .miniapp_helpers.payment_status.dispatcher import (
    resolve_payment_status_entry as _resolve_payment_status_entry_impl,
)
from .miniapp_helpers.payment_status.gateway import (
    resolve_pal24_payment_status as _resolve_pal24_payment_status_impl,
    resolve_wata_payment_status as _resolve_wata_payment_status_impl,
)
from .miniapp_helpers.promo.discount import extract_promo_discounts
from .miniapp_helpers.promo.offer import (
    extract_offer_extra,
    normalize_effect_type,
)
from .miniapp_helpers.promo_models import (
    ActiveOfferContext,
    build_promo_offer_models,
    find_active_test_access_offers,
)
from .miniapp_helpers.referral import build_referral_info
from .miniapp_helpers.runtime import (
    load_devices_info,
    load_subscription_links,
    resolve_connected_servers,
)
from .miniapp_helpers.subscription.common import (
    validate_subscription_id as _validate_subscription_id_impl,
)
from .miniapp_helpers.subscription.devices_update import (
    calculate_devices_upgrade_cost,
    charge_devices_upgrade,
    resolve_device_limits,
)
from .miniapp_helpers.subscription.renewal import (
    prepare_subscription_renewal_options,
)
from .miniapp_helpers.subscription.renewal_execute import (
    execute_classic_renewal,
    execute_tariff_renewal,
)
from .miniapp_helpers.subscription.renewal_payment import (
    create_renewal_cryptobot_payment,
)
from .miniapp_helpers.subscription.renewal_submit import (
    build_tariff_renewal_pricing,
    ensure_classic_renewal_period_available,
    ensure_renewal_method_or_balance,
    ensure_renewal_method_supported,
    resolve_renewal_method,
    resolve_renewal_period,
)
from .miniapp_helpers.subscription.servers_update import (
    apply_servers_update_plan,
    build_servers_update_plan,
    resolve_selected_server_order,
    resolve_server_changes,
)
from .miniapp_helpers.subscription.settings import (
    build_subscription_settings,
)
from .miniapp_helpers.subscription.traffic_update import (
    calculate_traffic_upgrade_cost,
    charge_traffic_upgrade,
    ensure_traffic_update_allowed,
    resolve_new_traffic_value,
)
from .miniapp_helpers.subscription.update_finalize import (
    finalize_subscription_update,
)
from .miniapp_helpers.tariff.base import ensure_tariffs_mode_enabled
from .miniapp_helpers.tariff.daily import (
    build_daily_toggle_message,
    ensure_daily_resume_allowed,
    get_daily_tariff_for_subscription,
    sync_daily_resume_if_needed,
    toggle_pause_state,
)
from .miniapp_helpers.tariff.listing import build_tariffs_payload
from .miniapp_helpers.tariff.purchase import (
    build_tariff_purchase_context,
    ensure_tariff_purchase_balance,
)
from .miniapp_helpers.tariff.switch_context import resolve_tariff_switch_context
from .miniapp_helpers.tariff.switch_flow import (
    apply_tariff_switch_to_subscription,
    build_switch_charge_description,
    build_switch_result_message,
    calculate_switch_pricing,
    ensure_switch_balance,
    execute_switch_charge,
    resolve_tariff_squads,
)
from .miniapp_helpers.tariff.topup import (
    build_topup_description,
    calculate_topup_price,
    ensure_topup_balance,
    execute_topup_purchase,
    get_tariff_for_topup,
    validate_topup_package,
)
from .miniapp_helpers.tariff_state import (
    get_current_tariff_model,
    is_trial_available_for_user,
)
from .miniapp_misc_helpers import (
    is_remnawave_configured,
    resolve_display_name,
    serialize_transaction,
)
from .miniapp_purchase_selection_helpers import merge_purchase_selection_from_request
from .miniapp_renewal_message_helpers import (
    build_promo_offer_payload,
    build_renewal_pending_message,
    build_renewal_status_message,
    build_renewal_success_message,
)


logger = structlog.get_logger(__name__)

router = APIRouter()

promo_code_service = PromoCodeService()
renewal_service = SubscriptionRenewalService()


# Backward-compatible aliases used by existing tests and monkeypatches.
async def _resolve_user_from_init_data(db: AsyncSession, init_data: str):
    return await _resolve_user_from_init_data_impl(db, init_data)


async def _authorize_miniapp_user(init_data: str, db: AsyncSession):
    return await _authorize_miniapp_user_impl(init_data, db)


def _ensure_paid_subscription(user, allowed_statuses: set[str] | None = None):
    return _ensure_paid_subscription_impl(user, allowed_statuses=allowed_statuses)


def _validate_subscription_id(subscription_id: int | None, subscription) -> None:
    _validate_subscription_id_impl(subscription_id, subscription)


async def _calculate_subscription_renewal_pricing(
    db: AsyncSession,
    user,
    subscription,
    period_days: int,
):
    return await renewal_service.calculate_pricing(db, user, subscription, period_days)


async def _get_usd_to_rub_rate() -> float:
    return await _get_usd_to_rub_rate_impl()


def _compute_cryptobot_limits(rate: float) -> tuple[int, int]:
    return _compute_cryptobot_limits_impl(rate)


def _classify_status(status: str | None, is_paid: bool) -> str:
    return classify_payment_status(status, is_paid)


async def _resolve_payment_status_entry(*, payment_service: PaymentService, db: AsyncSession, user, query):
    return await _resolve_payment_status_entry_impl(
        payment_service=payment_service,
        db=db,
        user=user,
        query=query,
    )


async def _resolve_yookassa_payment_status(db: AsyncSession, user, query):
    return await _resolve_yookassa_payment_status_impl(db, user, query, method='yookassa')


async def _resolve_pal24_payment_status(payment_service: PaymentService, db: AsyncSession, user, query):
    return await _resolve_pal24_payment_status_impl(payment_service, db, user, query)


async def _resolve_wata_payment_status(payment_service: PaymentService, db: AsyncSession, user, query):
    local_payment_id = query.local_payment_id
    payment_link_id = query.payment_link_id or query.payment_id or query.invoice_id

    if not local_payment_id and payment_link_id:
        fallback_payment = await get_wata_payment_by_link_id(db, payment_link_id)
        if fallback_payment:
            query = query.model_copy(update={'local_payment_id': fallback_payment.id})

    return await _resolve_wata_payment_status_impl(payment_service, db, user, query)


async def _find_recent_deposit(
    db: AsyncSession,
    *,
    user_id: int,
    payment_method,
    amount_kopeks: int | None,
    started_at: datetime | None,
):
    return await _find_recent_deposit_impl(
        db,
        user_id=user_id,
        payment_method=payment_method,
        amount_kopeks=amount_kopeks,
        started_at=started_at,
    )


@router.post(
    '/maintenance/status',
    response_model=MiniAppMaintenanceStatusResponse,
)
async def get_maintenance_status(
    payload: MiniAppSubscriptionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppMaintenanceStatusResponse:
    _, _ = await _resolve_user_from_init_data(db, payload.init_data)
    status_info = maintenance_service.get_status_info()
    return MiniAppMaintenanceStatusResponse(
        is_active=bool(status_info.get('is_active')),
        message=maintenance_service.get_maintenance_message(),
        reason=status_info.get('reason'),
    )


@router.post(
    '/payments/methods',
    response_model=MiniAppPaymentMethodsResponse,
)
async def get_payment_methods(
    payload: MiniAppPaymentMethodsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPaymentMethodsResponse:
    _, _ = await _resolve_user_from_init_data(db, payload.init_data)

    methods: list[MiniAppPaymentMethod] = []

    if settings.TELEGRAM_STARS_ENABLED:
        stars_min_amount = compute_stars_min_amount()
        methods.append(
            MiniAppPaymentMethod(
                id='stars',
                icon='⭐',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=stars_min_amount,
                amount_step_kopeks=stars_min_amount,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_yookassa_enabled():
        if getattr(settings, 'YOOKASSA_SBP_ENABLED', False):
            methods.append(
                MiniAppPaymentMethod(
                    id='yookassa_sbp',
                    icon='🏦',
                    requires_amount=True,
                    currency='RUB',
                    min_amount_kopeks=settings.YOOKASSA_MIN_AMOUNT_KOPEKS,
                    max_amount_kopeks=settings.YOOKASSA_MAX_AMOUNT_KOPEKS,
                    integration_type=MiniAppPaymentIntegrationType.REDIRECT,
                )
            )

        methods.append(
            MiniAppPaymentMethod(
                id='yookassa',
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.YOOKASSA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.YOOKASSA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_mulenpay_enabled():
        mulenpay_iframe_config = build_mulenpay_iframe_config()
        mulenpay_integration = (
            MiniAppPaymentIntegrationType.IFRAME if mulenpay_iframe_config else MiniAppPaymentIntegrationType.REDIRECT
        )
        methods.append(
            MiniAppPaymentMethod(
                id='mulenpay',
                name=settings.get_mulenpay_display_name(),
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.MULENPAY_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.MULENPAY_MAX_AMOUNT_KOPEKS,
                integration_type=mulenpay_integration,
                iframe_config=mulenpay_iframe_config,
            )
        )

    if settings.is_pal24_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='pal24',
                icon='🏦',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.PAL24_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.PAL24_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
                options=[
                    MiniAppPaymentOption(
                        id='sbp',
                        icon='🏦',
                        title_key='topup.method.pal24.option.sbp.title',
                        description_key='topup.method.pal24.option.sbp.description',
                        title='Faster Payments (SBP)',
                        description='Instant SBP transfer with no fees.',
                    ),
                    MiniAppPaymentOption(
                        id='card',
                        icon='💳',
                        title_key='topup.method.pal24.option.card.title',
                        description_key='topup.method.pal24.option.card.description',
                        title='Bank card',
                        description='Pay with a bank card via PayPalych.',
                    ),
                ],
            )
        )

    if settings.is_wata_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='wata',
                icon='🌊',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.WATA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.WATA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_platega_enabled() and settings.get_platega_active_methods():
        platega_methods = settings.get_platega_active_methods()
        definitions = settings.get_platega_method_definitions()
        options: list[MiniAppPaymentOption] = []

        for method_code in platega_methods:
            info = definitions.get(method_code, {})
            options.append(
                MiniAppPaymentOption(
                    id=str(method_code),
                    icon=info.get('icon') or ('🏦' if method_code == 2 else '💳'),
                    title_key=f'topup.method.platega.option.{method_code}.title',
                    description_key=f'topup.method.platega.option.{method_code}.description',
                    title=info.get('title') or info.get('name') or f'Platega {method_code}',
                    description=info.get('description') or info.get('name'),
                )
            )

        methods.append(
            MiniAppPaymentMethod(
                id='platega',
                icon='💳',
                requires_amount=True,
                currency=settings.PLATEGA_CURRENCY,
                min_amount_kopeks=settings.PLATEGA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.PLATEGA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
                options=options,
            )
        )

    if settings.is_cryptobot_enabled():
        rate = await _get_usd_to_rub_rate()
        min_amount_kopeks, max_amount_kopeks = _compute_cryptobot_limits(rate)
        methods.append(
            MiniAppPaymentMethod(
                id='cryptobot',
                icon='🪙',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=min_amount_kopeks,
                max_amount_kopeks=max_amount_kopeks,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_heleket_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='heleket',
                icon='🪙',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=100 * 100,
                max_amount_kopeks=100_000 * 100,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_cloudpayments_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='cloudpayments',
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.CLOUDPAYMENTS_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.CLOUDPAYMENTS_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_freekassa_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='freekassa',
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.FREEKASSA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.FREEKASSA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.TRIBUTE_ENABLED:
        methods.append(
            MiniAppPaymentMethod(
                id='tribute',
                icon='💎',
                requires_amount=False,
                currency='RUB',
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    order_map = {
        'stars': 1,
        'yookassa_sbp': 2,
        'yookassa': 3,
        'cloudpayments': 4,
        'freekassa': 5,
        'mulenpay': 6,
        'pal24': 7,
        'platega': 8,
        'wata': 9,
        'cryptobot': 10,
        'heleket': 11,
        'tribute': 12,
    }
    methods.sort(key=lambda item: order_map.get(item.id, 99))

    return MiniAppPaymentMethodsResponse(methods=methods)


@router.post(
    '/payments/create',
    response_model=MiniAppPaymentCreateResponse,
)
async def create_payment_link(
    payload: MiniAppPaymentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPaymentCreateResponse:
    user, _ = await _resolve_user_from_init_data(db, payload.init_data)

    method = resolve_create_payment_method(payload.method)
    amount_kopeks = resolve_create_payment_amount(
        amount_rubles=payload.amount_rubles,
        amount_kopeks=payload.amount_kopeks,
    )

    if method == 'stars':
        if not settings.TELEGRAM_STARS_ENABLED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if not settings.BOT_TOKEN:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Bot token is not configured')

        requested_amount_kopeks = amount_kopeks
        try:
            stars_amount, amount_kopeks = normalize_stars_amount(amount_kopeks)
        except ValueError as exc:
            logger.error('Failed to normalize Stars amount', exc=exc)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to prepare Stars payment',
            ) from exc

        bot = Bot(token=settings.BOT_TOKEN)
        invoice_payload = build_balance_invoice_payload(user.id, amount_kopeks)
        try:
            payment_service = PaymentService(bot)
            invoice_link = await payment_service.create_stars_invoice(
                amount_kopeks=amount_kopeks,
                description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
                payload=invoice_payload,
                stars_amount=stars_amount,
            )
        finally:
            await bot.session.close()

        if not invoice_link:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create invoice')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=invoice_link,
            amount_kopeks=amount_kopeks,
            extra={
                'invoice_payload': invoice_payload,
                'requested_at': current_request_timestamp(),
                'stars_amount': stars_amount,
                'requested_amount_kopeks': requested_amount_kopeks,
            },
        )

    if method == 'yookassa_sbp':
        return await create_yookassa_sbp_balance_payment_response(
            db=db,
            user=user,
            amount_kopeks=amount_kopeks,
        )

    if method == 'yookassa':
        return await create_yookassa_balance_payment_response(
            db=db,
            user=user,
            amount_kopeks=amount_kopeks,
        )

    if method == 'mulenpay':
        if not settings.is_mulenpay_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.MULENPAY_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.MULENPAY_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        payment_service = PaymentService()
        result = await payment_service.create_mulenpay_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language,
        )
        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'payment_id': result.get('mulen_payment_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'platega':
        if not settings.is_platega_enabled() or not settings.get_platega_active_methods():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.PLATEGA_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.PLATEGA_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        active_methods = settings.get_platega_active_methods()
        method_option = payload.payment_option or str(active_methods[0])
        try:
            method_code = int(str(method_option).strip())
        except (TypeError, ValueError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Invalid Platega payment option')

        if method_code not in active_methods:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Selected Platega method is unavailable')

        payment_service = PaymentService()
        result = await payment_service.create_platega_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language or settings.DEFAULT_LANGUAGE,
            payment_method_code=method_code,
        )

        redirect_url = result.get('redirect_url') if result else None
        if not result or not redirect_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=redirect_url,
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'payment_id': result.get('transaction_id'),
                'correlation_id': result.get('correlation_id'),
                'selected_option': str(method_code),
                'payload': result.get('payload'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'wata':
        if not settings.is_wata_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.WATA_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.WATA_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        payment_service = PaymentService()
        result = await payment_service.create_wata_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language,
        )
        payment_url = result.get('payment_url') if result else None
        if not result or not payment_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=payment_url,
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'payment_link_id': result.get('payment_link_id'),
                'payment_id': result.get('payment_link_id'),
                'status': result.get('status'),
                'order_id': result.get('order_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'pal24':
        if not settings.is_pal24_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.PAL24_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.PAL24_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        option = (payload.payment_option or '').strip().lower()
        if option not in {'card', 'sbp'}:
            option = 'sbp'
        provider_method = 'card' if option == 'card' else 'sbp'

        payment_service = PaymentService()
        result = await payment_service.create_pal24_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language or settings.DEFAULT_LANGUAGE,
            payment_method=provider_method,
        )
        if not result:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        preferred_urls: list[str | None] = []
        if option == 'sbp':
            preferred_urls.append(result.get('sbp_url') or result.get('transfer_url'))
        elif option == 'card':
            preferred_urls.append(result.get('card_url'))
        preferred_urls.extend(
            [
                result.get('link_url'),
                result.get('link_page_url'),
                result.get('payment_url'),
                result.get('transfer_url'),
            ]
        )
        payment_url = next((url for url in preferred_urls if url), None)
        if not payment_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to obtain payment url')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=payment_url,
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'bill_id': result.get('bill_id'),
                'order_id': result.get('order_id'),
                'payment_method': result.get('payment_method') or provider_method,
                'sbp_url': result.get('sbp_url') or result.get('transfer_url'),
                'card_url': result.get('card_url'),
                'link_url': result.get('link_url'),
                'link_page_url': result.get('link_page_url'),
                'transfer_url': result.get('transfer_url'),
                'selected_option': option,
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'cryptobot':
        return await create_cryptobot_balance_payment_response(
            db=db,
            user=user,
            amount_kopeks=amount_kopeks,
        )

    if method == 'heleket':
        if not settings.is_heleket_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

        min_amount_kopeks = 100 * 100
        max_amount_kopeks = 100_000 * 100
        if amount_kopeks < min_amount_kopeks:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount is below minimum ({min_amount_kopeks / 100:.2f} RUB)',
            )
        if amount_kopeks > max_amount_kopeks:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount exceeds maximum ({max_amount_kopeks / 100:.2f} RUB)',
            )

        payment_service = PaymentService()
        result = await payment_service.create_heleket_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language or settings.DEFAULT_LANGUAGE,
        )

        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'uuid': result.get('uuid'),
                'order_id': result.get('order_id'),
                'payer_amount': result.get('payer_amount'),
                'payer_currency': result.get('payer_currency'),
                'discount_percent': result.get('discount_percent'),
                'exchange_rate': result.get('exchange_rate'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'cloudpayments':
        if not settings.is_cloudpayments_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

        if amount_kopeks < settings.CLOUDPAYMENTS_MIN_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount is below minimum ({settings.CLOUDPAYMENTS_MIN_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )
        if amount_kopeks > settings.CLOUDPAYMENTS_MAX_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount exceeds maximum ({settings.CLOUDPAYMENTS_MAX_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )

        payment_service = PaymentService()
        result = await payment_service.create_cloudpayments_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            telegram_id=user.telegram_id,
            language=user.language or settings.DEFAULT_LANGUAGE,
        )

        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('payment_id'),
                'invoice_id': result.get('invoice_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'freekassa':
        if not settings.is_freekassa_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

        if amount_kopeks < settings.FREEKASSA_MIN_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount is below minimum ({settings.FREEKASSA_MIN_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )
        if amount_kopeks > settings.FREEKASSA_MAX_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount exceeds maximum ({settings.FREEKASSA_MAX_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )

        payment_service = PaymentService()
        result = await payment_service.create_freekassa_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            email=getattr(user, 'email', None),
            language=user.language or settings.DEFAULT_LANGUAGE,
        )

        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'order_id': result.get('order_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'tribute':
        if not settings.TRIBUTE_ENABLED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if not settings.BOT_TOKEN:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Bot token is not configured')

        bot = Bot(token=settings.BOT_TOKEN)
        try:
            tribute_service = TributeService(bot)
            payment_url = await tribute_service.create_payment_link(
                user_id=user.telegram_id,
                amount_kopeks=amount_kopeks or 0,
                description=settings.get_balance_payment_description(amount_kopeks or 0),
            )
        finally:
            await bot.session.close()

        if not payment_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=payment_url,
            amount_kopeks=amount_kopeks,
            extra={
                'requested_at': current_request_timestamp(),
            },
        )

    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Unknown payment method')


@router.post(
    '/payments/status',
    response_model=MiniAppPaymentStatusResponse,
)
async def get_payment_statuses(
    payload: MiniAppPaymentStatusRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPaymentStatusResponse:
    user, _ = await _resolve_user_from_init_data(db, payload.init_data)

    entries = payload.payments or []
    if not entries:
        return MiniAppPaymentStatusResponse(results=[])

    payment_service = PaymentService()
    results: list[MiniAppPaymentStatusResult] = []

    for entry in entries:
        result = await _resolve_payment_status_entry(
            payment_service=payment_service,
            db=db,
            user=user,
            query=entry,
        )
        if result:
            results.append(result)

    return MiniAppPaymentStatusResponse(results=results)


async def _resolve_payment_status_entry(
    *,
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    method = (query.method or '').strip().lower()
    if not method:
        return MiniAppPaymentStatusResult(
            method='',
            status='unknown',
            message='Payment method is required',
        )

    if method in {'yookassa', 'yookassa_sbp'}:
        return await _resolve_yookassa_payment_status(
            db,
            user,
            query,
            method=method,
        )
    if method == 'mulenpay':
        return await _resolve_mulenpay_payment_status(payment_service, db, user, query)
    if method == 'platega':
        return await _resolve_platega_payment_status(payment_service, db, user, query)
    if method == 'wata':
        return await _resolve_wata_payment_status(payment_service, db, user, query)
    if method == 'pal24':
        return await _resolve_pal24_payment_status(payment_service, db, user, query)
    if method == 'cryptobot':
        return await _resolve_cryptobot_payment_status(db, user, query)
    if method == 'heleket':
        return await _resolve_heleket_payment_status(db, user, query)
    if method == 'cloudpayments':
        return await _resolve_cloudpayments_payment_status(db, user, query)
    if method == 'freekassa':
        return await _resolve_freekassa_payment_status(db, user, query)
    if method == 'stars':
        return await _resolve_stars_payment_status(db, user, query)
    if method == 'tribute':
        return await _resolve_tribute_payment_status(db, user, query)

    return MiniAppPaymentStatusResult(
        method=method,
        status='unknown',
        message='Unsupported payment method',
    )


async def _resolve_yookassa_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
    *,
    method: str = 'yookassa',
) -> MiniAppPaymentStatusResult:
    from app.database.crud.yookassa import (
        get_yookassa_payment_by_id,
        get_yookassa_payment_by_local_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_yookassa_payment_by_local_id(db, query.local_payment_id)
    if not payment and query.payment_id:
        payment = await get_yookassa_payment_by_id(db, query.payment_id)

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method=method,
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'payment_id': query.payment_id,
                'invoice_id': query.payment_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    succeeded = bool(payment.is_paid and (payment.status or '').lower() == 'succeeded')
    status = _classify_status(payment.status, succeeded)
    completed_at = payment.captured_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method=method,
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.yookassa_payment_id,
        extra={
            'status': payment.status,
            'is_paid': payment.is_paid,
            'local_payment_id': payment.id,
            'payment_id': payment.yookassa_payment_id,
            'invoice_id': payment.yookassa_payment_id,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def _resolve_mulenpay_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    if not query.local_payment_id:
        return MiniAppPaymentStatusResult(
            method='mulenpay',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Missing payment identifier',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payment_id': query.payment_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_info = await payment_service.get_mulenpay_payment_status(db, query.local_payment_id)
    payment = status_info.get('payment') if status_info else None

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='mulenpay',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payment_id': query.payment_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_raw = status_info.get('status') or payment.status
    is_paid = bool(payment.is_paid)
    status = _classify_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at
    message = None
    if status == 'failed':
        remote_status = status_info.get('remote_status_code') or status_raw
        if remote_status:
            message = f'Status: {remote_status}'

    return MiniAppPaymentStatusResult(
        method='mulenpay',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=str(payment.mulen_payment_id or payment.uuid),
        message=message,
        extra={
            'status': payment.status,
            'remote_status': status_info.get('remote_status_code'),
            'local_payment_id': payment.id,
            'payment_id': payment.mulen_payment_id,
            'uuid': str(payment.uuid),
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def _resolve_platega_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.platega import (
        get_platega_payment_by_correlation_id,
        get_platega_payment_by_id,
        get_platega_payment_by_transaction_id,
    )

    payment = None
    local_id = query.local_payment_id
    if local_id:
        payment = await get_platega_payment_by_id(db, local_id)

    if not payment and query.payment_id:
        payment = await get_platega_payment_by_transaction_id(db, query.payment_id)

    if not payment and query.payload:
        correlation = str(query.payload).replace('platega:', '')
        payment = await get_platega_payment_by_correlation_id(db, correlation)

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='platega',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'payment_id': query.payment_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_info = await payment_service.get_platega_payment_status(db, payment.id)
    refreshed_payment = (status_info or {}).get('payment') or payment

    status_raw = (status_info or {}).get('status') or getattr(payment, 'status', None)
    is_paid_flag = bool((status_info or {}).get('is_paid') or getattr(payment, 'is_paid', False))
    status_value = _classify_status(status_raw, is_paid_flag)

    completed_at = (
        getattr(refreshed_payment, 'paid_at', None)
        or getattr(refreshed_payment, 'updated_at', None)
        or getattr(refreshed_payment, 'created_at', None)
    )

    extra: dict[str, Any] = {
        'local_payment_id': refreshed_payment.id,
        'payment_id': refreshed_payment.platega_transaction_id,
        'correlation_id': refreshed_payment.correlation_id,
        'status': status_raw,
        'is_paid': getattr(refreshed_payment, 'is_paid', False),
        'payload': query.payload,
        'started_at': query.started_at,
    }

    if status_info and status_info.get('remote'):
        extra['remote'] = status_info.get('remote')

    return MiniAppPaymentStatusResult(
        method='platega',
        status=status_value,
        is_paid=status_value == 'paid',
        amount_kopeks=refreshed_payment.amount_kopeks,
        currency=refreshed_payment.currency,
        completed_at=completed_at,
        transaction_id=refreshed_payment.transaction_id,
        external_id=refreshed_payment.platega_transaction_id,
        message=None,
        extra=extra,
    )


async def _resolve_wata_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    local_id = query.local_payment_id
    payment_link_id = query.payment_link_id or query.payment_id or query.invoice_id
    fallback_payment = None

    if not local_id and payment_link_id:
        fallback_payment = await get_wata_payment_by_link_id(db, payment_link_id)
        if fallback_payment:
            local_id = fallback_payment.id

    if not local_id:
        return MiniAppPaymentStatusResult(
            method='wata',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Missing payment identifier',
            extra={
                'local_payment_id': query.local_payment_id,
                'payment_link_id': payment_link_id,
                'payment_id': query.payment_id,
                'invoice_id': query.invoice_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_info = await payment_service.get_wata_payment_status(db, local_id)
    payment = (status_info or {}).get('payment') or fallback_payment

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='wata',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': local_id,
                'payment_link_id': (payment_link_id or getattr(payment, 'payment_link_id', None)),
                'payment_id': query.payment_id,
                'invoice_id': query.invoice_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    remote_link = (status_info or {}).get('remote_link') if status_info else None
    transaction_payload = (status_info or {}).get('transaction') if status_info else None
    status_raw = (status_info or {}).get('status') or getattr(payment, 'status', None)
    is_paid_flag = bool((status_info or {}).get('is_paid') or getattr(payment, 'is_paid', False))
    status_value = _classify_status(status_raw, is_paid_flag)
    completed_at = (
        getattr(payment, 'paid_at', None)
        or getattr(payment, 'updated_at', None)
        or getattr(payment, 'created_at', None)
    )

    message = None
    if status_value == 'failed':
        message = (
            (transaction_payload or {}).get('errorDescription')
            or (transaction_payload or {}).get('errorCode')
            or (remote_link or {}).get('status')
        )

    extra: dict[str, Any] = {
        'local_payment_id': payment.id,
        'payment_link_id': payment.payment_link_id,
        'payment_id': payment.payment_link_id,
        'status': status_raw,
        'is_paid': getattr(payment, 'is_paid', False),
        'order_id': getattr(payment, 'order_id', None),
        'payload': query.payload,
        'started_at': query.started_at,
    }
    if remote_link:
        extra['remote_link'] = remote_link
    if transaction_payload:
        extra['transaction'] = transaction_payload

    return MiniAppPaymentStatusResult(
        method='wata',
        status=status_value,
        is_paid=status_value == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.payment_link_id,
        message=message,
        extra=extra,
    )


async def _resolve_pal24_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.pal24 import get_pal24_payment_by_bill_id

    local_id = query.local_payment_id
    if not local_id and query.invoice_id:
        payment_by_bill = await get_pal24_payment_by_bill_id(db, query.invoice_id)
        if payment_by_bill and payment_by_bill.user_id == user.id:
            local_id = payment_by_bill.id

    if not local_id:
        return MiniAppPaymentStatusResult(
            method='pal24',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Missing payment identifier',
            extra={
                'local_payment_id': query.local_payment_id,
                'bill_id': query.invoice_id,
                'order_id': None,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_info = await payment_service.get_pal24_payment_status(db, local_id)
    payment = status_info.get('payment') if status_info else None

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='pal24',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': local_id,
                'bill_id': query.invoice_id,
                'order_id': None,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_raw = status_info.get('status') or payment.status
    is_paid = bool(payment.is_paid)
    status = _classify_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at
    message = None
    if status == 'failed':
        remote_status = status_info.get('remote_status') or status_raw
        if remote_status:
            message = f'Status: {remote_status}'

    links_info = status_info.get('links') if status_info else {}

    return MiniAppPaymentStatusResult(
        method='pal24',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.bill_id,
        message=message,
        extra={
            'status': payment.status,
            'remote_status': status_info.get('remote_status'),
            'local_payment_id': payment.id,
            'bill_id': payment.bill_id,
            'order_id': payment.order_id,
            'payment_method': getattr(payment, 'payment_method', None),
            'payload': query.payload,
            'started_at': query.started_at,
            'links': links_info or None,
            'sbp_url': status_info.get('sbp_url') if status_info else None,
            'card_url': status_info.get('card_url') if status_info else None,
            'link_url': status_info.get('link_url') if status_info else None,
            'link_page_url': status_info.get('link_page_url') if status_info else None,
            'primary_url': status_info.get('primary_url') if status_info else None,
            'secondary_url': status_info.get('secondary_url') if status_info else None,
            'selected_method': status_info.get('selected_method') if status_info else None,
        },
    )


async def _resolve_cryptobot_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.cryptobot import (
        get_cryptobot_payment_by_id,
        get_cryptobot_payment_by_invoice_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_cryptobot_payment_by_id(db, query.local_payment_id)
    if not payment and query.invoice_id:
        payment = await get_cryptobot_payment_by_invoice_id(db, query.invoice_id)

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='cryptobot',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payment_id': query.payment_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_raw = payment.status
    is_paid = (status_raw or '').lower() == 'paid'
    status = _classify_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    amount_kopeks = None
    try:
        amount_kopeks = int(Decimal(payment.amount) * Decimal(100))
    except (InvalidOperation, TypeError):
        amount_kopeks = None

    descriptor = decode_payment_payload(getattr(payment, 'payload', '') or '', expected_user_id=user.id)
    purpose = 'subscription_renewal' if descriptor else 'balance_topup'

    return MiniAppPaymentStatusResult(
        method='cryptobot',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=amount_kopeks,
        currency=payment.asset,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.invoice_id,
        extra={
            'status': payment.status,
            'asset': payment.asset,
            'local_payment_id': payment.id,
            'invoice_id': payment.invoice_id,
            'payload': query.payload,
            'started_at': query.started_at,
            'purpose': purpose,
            'subscription_id': descriptor.subscription_id if descriptor else None,
            'period_days': descriptor.period_days if descriptor else None,
        },
    )


async def _resolve_heleket_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.heleket import (
        get_heleket_payment_by_id,
        get_heleket_payment_by_order_id,
        get_heleket_payment_by_uuid,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_heleket_payment_by_id(db, query.local_payment_id)
    if not payment and query.payment_id:
        payment = await get_heleket_payment_by_uuid(db, query.payment_id)
    if not payment and query.invoice_id:
        payment = await get_heleket_payment_by_uuid(db, query.invoice_id)
    if not payment and query.bill_id:
        payment = await get_heleket_payment_by_order_id(db, query.bill_id)

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='heleket',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'uuid': query.payment_id or query.invoice_id,
                'order_id': query.bill_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_raw = payment.status
    is_paid = bool(payment.is_paid)
    status = _classify_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method='heleket',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.uuid,
        message=None,
        extra={
            'status': payment.status,
            'local_payment_id': payment.id,
            'uuid': payment.uuid,
            'order_id': payment.order_id,
            'payer_amount': payment.payer_amount,
            'payer_currency': payment.payer_currency,
            'discount_percent': payment.discount_percent,
            'exchange_rate': payment.exchange_rate,
            'payment_url': payment.payment_url,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def _resolve_cloudpayments_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.cloudpayments import (
        get_cloudpayments_payment_by_id,
        get_cloudpayments_payment_by_invoice_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_cloudpayments_payment_by_id(db, query.local_payment_id)
    if not payment and query.invoice_id:
        payment = await get_cloudpayments_payment_by_invoice_id(db, query.invoice_id)
    if not payment and query.payment_id:
        payment = await get_cloudpayments_payment_by_invoice_id(db, query.payment_id)

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='cloudpayments',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_raw = payment.status
    is_paid = bool(payment.is_paid)
    status = _classify_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method='cloudpayments',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.invoice_id,
        message=None,
        extra={
            'status': payment.status,
            'local_payment_id': payment.id,
            'invoice_id': payment.invoice_id,
            'transaction_id_cp': payment.transaction_id_cp,
            'card_type': payment.card_type,
            'card_last_four': payment.card_last_four,
            'payment_url': payment.payment_url,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def _resolve_freekassa_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.freekassa import (
        get_freekassa_payment_by_id,
        get_freekassa_payment_by_order_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_freekassa_payment_by_id(db, query.local_payment_id)
    if not payment and query.payment_id:
        payment = await get_freekassa_payment_by_order_id(db, query.payment_id)

    if not payment or payment.user_id != user.id:
        return MiniAppPaymentStatusResult(
            method='freekassa',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'order_id': query.payment_id,
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    status_raw = payment.status
    is_paid = bool(payment.is_paid)
    status = _classify_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method='freekassa',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.freekassa_order_id,
        message=None,
        extra={
            'status': payment.status,
            'local_payment_id': payment.id,
            'order_id': payment.order_id,
            'freekassa_order_id': payment.freekassa_order_id,
            'payment_url': payment.payment_url,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def _resolve_stars_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    started_at = _parse_client_timestamp(query.started_at)
    transaction = await _find_recent_deposit(
        db,
        user_id=user.id,
        payment_method=PaymentMethod.TELEGRAM_STARS,
        amount_kopeks=query.amount_kopeks,
        started_at=started_at,
    )

    if not transaction:
        return MiniAppPaymentStatusResult(
            method='stars',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Waiting for confirmation',
            extra={
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    return MiniAppPaymentStatusResult(
        method='stars',
        status='paid',
        is_paid=True,
        amount_kopeks=transaction.amount_kopeks,
        currency='RUB',
        completed_at=transaction.completed_at or transaction.created_at,
        transaction_id=transaction.id,
        external_id=transaction.external_id,
        extra={
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def _resolve_tribute_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    started_at = _parse_client_timestamp(query.started_at)
    transaction = await _find_recent_deposit(
        db,
        user_id=user.id,
        payment_method=PaymentMethod.TRIBUTE,
        amount_kopeks=query.amount_kopeks,
        started_at=started_at,
    )

    if not transaction:
        return MiniAppPaymentStatusResult(
            method='tribute',
            status='pending',
            is_paid=False,
            amount_kopeks=query.amount_kopeks,
            message='Waiting for confirmation',
            extra={
                'payload': query.payload,
                'started_at': query.started_at,
            },
        )

    return MiniAppPaymentStatusResult(
        method='tribute',
        status='paid',
        is_paid=True,
        amount_kopeks=transaction.amount_kopeks,
        currency='RUB',
        completed_at=transaction.completed_at or transaction.created_at,
        transaction_id=transaction.id,
        external_id=transaction.external_id,
        extra={
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


_TEMPLATE_ID_PATTERN = re.compile(r'promo_template_(?P<template_id>\d+)$')
_OFFER_TYPE_ICONS = {
    'extend_discount': '💎',
    'purchase_discount': '🎯',
    'test_access': '🧪',
}
_EFFECT_TYPE_ICONS = {
    'percent_discount': '🎁',
    'test_access': '🧪',
    'balance_bonus': '💰',
}
_DEFAULT_OFFER_ICON = '🎉'

ActiveOfferContext = tuple[Any, int | None, datetime | None]


def _extract_template_id(notification_type: str | None) -> int | None:
    if not notification_type:
        return None

    match = _TEMPLATE_ID_PATTERN.match(notification_type)
    if not match:
        return None

    try:
        return int(match.group('template_id'))
    except (TypeError, ValueError):
        return None


def _extract_offer_extra(offer: Any) -> dict[str, Any]:
    extra = getattr(offer, 'extra_data', None)
    return extra if isinstance(extra, dict) else {}


def _extract_offer_type(offer: Any, template: PromoOfferTemplate | None) -> str | None:
    extra = _extract_offer_extra(offer)
    offer_type = extra.get('offer_type') if isinstance(extra.get('offer_type'), str) else None
    if offer_type:
        return offer_type
    template_type = getattr(template, 'offer_type', None)
    return template_type if isinstance(template_type, str) else None


def _normalize_effect_type(effect_type: str | None) -> str:
    normalized = (effect_type or 'percent_discount').strip().lower()
    if normalized == 'balance_bonus':
        return 'percent_discount'
    return normalized or 'percent_discount'


def _determine_offer_icon(offer_type: str | None, effect_type: str) -> str:
    if offer_type and offer_type in _OFFER_TYPE_ICONS:
        return _OFFER_TYPE_ICONS[offer_type]
    if effect_type in _EFFECT_TYPE_ICONS:
        return _EFFECT_TYPE_ICONS[effect_type]
    return _DEFAULT_OFFER_ICON


def _extract_offer_test_squad_uuids(offer: Any) -> list[str]:
    extra = _extract_offer_extra(offer)
    raw = extra.get('test_squad_uuids') or extra.get('squads') or []

    if isinstance(raw, str):
        raw = [raw]

    uuids: list[str] = []
    try:
        for item in raw:
            if not item:
                continue
            uuids.append(str(item))
    except TypeError:
        return []

    return uuids


def _format_offer_message(
    template: PromoOfferTemplate | None,
    offer: Any,
    *,
    server_name: str | None = None,
) -> str | None:
    message_template: str | None = None

    if template and isinstance(template.message_text, str):
        message_template = template.message_text
    else:
        extra = _extract_offer_extra(offer)
        raw_message = extra.get('message_text') or extra.get('text')
        if isinstance(raw_message, str):
            message_template = raw_message

    if not message_template:
        return None

    extra = _extract_offer_extra(offer)
    discount_percent = getattr(offer, 'discount_percent', None)
    try:
        discount_percent = int(discount_percent)
    except (TypeError, ValueError):
        discount_percent = None

    replacements: dict[str, Any] = {}
    if discount_percent is not None:
        replacements.setdefault('discount_percent', discount_percent)

    for key in ('valid_hours', 'active_discount_hours', 'test_duration_hours'):
        value = extra.get(key)
        if value is None and template is not None:
            template_value = getattr(template, key, None)
        else:
            template_value = None
        replacements.setdefault(key, value if value is not None else template_value)

    if replacements.get('active_discount_hours') is None and template:
        replacements['active_discount_hours'] = getattr(template, 'valid_hours', None)

    if replacements.get('test_duration_hours') is None and template:
        replacements['test_duration_hours'] = getattr(template, 'test_duration_hours', None)

    if server_name:
        replacements.setdefault('server_name', server_name)

    for key, value in extra.items():
        if isinstance(key, str) and key not in replacements and isinstance(value, (str, int, float)):
            replacements[key] = value

    try:
        return message_template.format(**replacements)
    except Exception:  # pragma: no cover - fallback for malformed templates
        return message_template


def _extract_offer_duration_hours(
    offer: Any,
    template: PromoOfferTemplate | None,
    effect_type: str,
) -> int | None:
    extra = _extract_offer_extra(offer)
    if effect_type == 'test_access':
        source = extra.get('test_duration_hours')
        if source is None and template is not None:
            source = getattr(template, 'test_duration_hours', None)
    else:
        source = extra.get('active_discount_hours')
        if source is None and template is not None:
            source = getattr(template, 'active_discount_hours', None)

    try:
        if source is None:
            return None
        hours = int(float(source))
        return hours if hours > 0 else None
    except (TypeError, ValueError):
        return None


def _format_bonus_label(amount_kopeks: int) -> str | None:
    if amount_kopeks <= 0:
        return None
    try:
        return settings.format_price(amount_kopeks)
    except Exception:  # pragma: no cover - defensive
        return f'{amount_kopeks / 100:.2f}'


async def _find_active_test_access_offers(
    db: AsyncSession,
    subscription: Subscription | None,
) -> list[ActiveOfferContext]:
    if not subscription or not getattr(subscription, 'id', None):
        return []

    now = datetime.now(UTC)
    result = await db.execute(
        select(SubscriptionTemporaryAccess)
        .options(selectinload(SubscriptionTemporaryAccess.offer))
        .where(
            SubscriptionTemporaryAccess.subscription_id == subscription.id,
            SubscriptionTemporaryAccess.is_active == True,
            SubscriptionTemporaryAccess.expires_at > now,
        )
        .order_by(SubscriptionTemporaryAccess.expires_at.desc())
    )

    entries = list(result.scalars().all())
    if not entries:
        return []

    offer_map: dict[int, tuple[Any, datetime | None]] = {}
    for entry in entries:
        offer = getattr(entry, 'offer', None)
        if not offer:
            continue

        effect_type = _normalize_effect_type(getattr(offer, 'effect_type', None))
        if effect_type != 'test_access':
            continue

        expires_at = getattr(entry, 'expires_at', None)
        if not expires_at or expires_at <= now:
            continue

        offer_id = getattr(offer, 'id', None)
        if not isinstance(offer_id, int):
            continue

        current = offer_map.get(offer_id)
        if current is None:
            offer_map[offer_id] = (offer, expires_at)
        else:
            _, current_expiry = current
            if current_expiry is None or (expires_at and expires_at > current_expiry):
                offer_map[offer_id] = (offer, expires_at)

    contexts: list[ActiveOfferContext] = []
    for offer_id, (offer, expires_at) in offer_map.items():
        contexts.append((offer, None, expires_at))

    contexts.sort(key=lambda item: item[2] or now, reverse=True)
    return contexts


async def _build_promo_offer_models(
    db: AsyncSession,
    available_offers: list[Any],
    active_offers: list[ActiveOfferContext] | None,
    *,
    user: User,
) -> list[MiniAppPromoOffer]:
    promo_offers: list[MiniAppPromoOffer] = []
    template_cache: dict[int, PromoOfferTemplate | None] = {}

    candidates: list[Any] = [offer for offer in available_offers if offer]
    active_offer_contexts: list[ActiveOfferContext] = []
    if active_offers:
        for offer, discount_override, expires_override in active_offers:
            if not offer:
                continue
            active_offer_contexts.append((offer, discount_override, expires_override))
            candidates.append(offer)

    squad_map: dict[str, MiniAppConnectedServer] = {}
    if candidates:
        all_uuids: list[str] = []
        for offer in candidates:
            all_uuids.extend(_extract_offer_test_squad_uuids(offer))
        if all_uuids:
            unique = list(dict.fromkeys(all_uuids))
            resolved = await _resolve_connected_servers(db, unique)
            squad_map = {server.uuid: server for server in resolved}

    async def get_template(template_id: int | None) -> PromoOfferTemplate | None:
        if not template_id:
            return None
        if template_id not in template_cache:
            template_cache[template_id] = await get_promo_offer_template_by_id(db, template_id)
        return template_cache[template_id]

    def build_test_squads(offer: Any) -> list[MiniAppConnectedServer]:
        test_squads: list[MiniAppConnectedServer] = []
        for uuid in _extract_offer_test_squad_uuids(offer):
            resolved = squad_map.get(uuid)
            if resolved:
                test_squads.append(MiniAppConnectedServer(uuid=resolved.uuid, name=resolved.name))
            else:
                test_squads.append(MiniAppConnectedServer(uuid=uuid, name=uuid))
        return test_squads

    def resolve_title(
        offer: Any,
        template: PromoOfferTemplate | None,
        offer_type: str | None,
    ) -> str | None:
        extra = _extract_offer_extra(offer)
        if isinstance(extra.get('title'), str) and extra['title'].strip():
            return extra['title'].strip()
        if template and template.name:
            return template.name
        if offer_type:
            return offer_type.replace('_', ' ').title()
        return None

    for offer in available_offers:
        template_id = _extract_template_id(getattr(offer, 'notification_type', None))
        template = await get_template(template_id)
        effect_type = _normalize_effect_type(getattr(offer, 'effect_type', None))
        offer_type = _extract_offer_type(offer, template)
        test_squads = build_test_squads(offer)
        server_name = test_squads[0].name if test_squads else None
        message_text = _format_offer_message(template, offer, server_name=server_name)
        bonus_label = _format_bonus_label(int(getattr(offer, 'bonus_amount_kopeks', 0) or 0))
        discount_percent = getattr(offer, 'discount_percent', 0)
        try:
            discount_percent = int(discount_percent)
        except (TypeError, ValueError):
            discount_percent = 0

        extra = _extract_offer_extra(offer)
        button_text = None
        if isinstance(extra.get('button_text'), str) and extra['button_text'].strip():
            button_text = extra['button_text'].strip()
        elif template and isinstance(template.button_text, str):
            button_text = template.button_text

        promo_offers.append(
            MiniAppPromoOffer(
                id=int(getattr(offer, 'id', 0) or 0),
                status='pending',
                notification_type=getattr(offer, 'notification_type', None),
                offer_type=offer_type,
                effect_type=effect_type,
                discount_percent=max(0, discount_percent),
                bonus_amount_kopeks=int(getattr(offer, 'bonus_amount_kopeks', 0) or 0),
                bonus_amount_label=bonus_label,
                expires_at=getattr(offer, 'expires_at', None),
                claimed_at=getattr(offer, 'claimed_at', None),
                is_active=bool(getattr(offer, 'is_active', False)),
                template_id=template_id,
                template_name=getattr(template, 'name', None),
                button_text=button_text,
                title=resolve_title(offer, template, offer_type),
                message_text=message_text,
                icon=_determine_offer_icon(offer_type, effect_type),
                test_squads=test_squads,
            )
        )

    if active_offer_contexts:
        seen_active_ids: set[int] = set()
        for active_offer_record, discount_override, expires_override in reversed(active_offer_contexts):
            offer_id = int(getattr(active_offer_record, 'id', 0) or 0)
            if offer_id and offer_id in seen_active_ids:
                continue
            if offer_id:
                seen_active_ids.add(offer_id)

            template_id = _extract_template_id(getattr(active_offer_record, 'notification_type', None))
            template = await get_template(template_id)
            effect_type = _normalize_effect_type(getattr(active_offer_record, 'effect_type', None))
            offer_type = _extract_offer_type(active_offer_record, template)
            show_active = False
            discount_value = discount_override if discount_override is not None else 0
            if (discount_value and discount_value > 0) or effect_type == 'test_access':
                show_active = True
            if not show_active:
                continue

            test_squads = build_test_squads(active_offer_record)
            server_name = test_squads[0].name if test_squads else None
            message_text = _format_offer_message(
                template,
                active_offer_record,
                server_name=server_name,
            )
            bonus_label = _format_bonus_label(int(getattr(active_offer_record, 'bonus_amount_kopeks', 0) or 0))

            started_at = getattr(active_offer_record, 'claimed_at', None)
            expires_at = expires_override or getattr(active_offer_record, 'expires_at', None)
            duration_seconds: int | None = None
            duration_hours = _extract_offer_duration_hours(active_offer_record, template, effect_type)
            if expires_at is None and duration_hours and started_at:
                expires_at = started_at + timedelta(hours=duration_hours)
            if expires_at and started_at:
                try:
                    duration_seconds = int((expires_at - started_at).total_seconds())
                except Exception:  # pragma: no cover - defensive
                    duration_seconds = None

            if (discount_value is None or discount_value <= 0) and effect_type != 'test_access':
                try:
                    discount_value = int(getattr(active_offer_record, 'discount_percent', 0) or 0)
                except (TypeError, ValueError):
                    discount_value = 0
            if discount_value is None:
                discount_value = 0

            extra = _extract_offer_extra(active_offer_record)
            button_text = None
            if isinstance(extra.get('button_text'), str) and extra['button_text'].strip():
                button_text = extra['button_text'].strip()
            elif template and isinstance(template.button_text, str):
                button_text = template.button_text

            promo_offers.insert(
                0,
                MiniAppPromoOffer(
                    id=offer_id,
                    status='active',
                    notification_type=getattr(active_offer_record, 'notification_type', None),
                    offer_type=offer_type,
                    effect_type=effect_type,
                    discount_percent=max(0, discount_value or 0),
                    bonus_amount_kopeks=int(getattr(active_offer_record, 'bonus_amount_kopeks', 0) or 0),
                    bonus_amount_label=bonus_label,
                    expires_at=getattr(active_offer_record, 'expires_at', None),
                    claimed_at=started_at,
                    is_active=False,
                    template_id=template_id,
                    template_name=getattr(template, 'name', None),
                    button_text=button_text,
                    title=resolve_title(active_offer_record, template, offer_type),
                    message_text=message_text,
                    icon=_determine_offer_icon(offer_type, effect_type),
                    test_squads=test_squads,
                    active_discount_expires_at=expires_at,
                    active_discount_started_at=started_at,
                    active_discount_duration_seconds=duration_seconds,
                ),
            )

    return promo_offers


def _bytes_to_gb(bytes_value: int | None) -> float:
    if not bytes_value:
        return 0.0
    return round(bytes_value / (1024**3), 2)


def _status_label(status: str) -> str:
    mapping = {
        'active': 'Active',
        'trial': 'Trial',
        'expired': 'Expired',
        'disabled': 'Disabled',
    }
    return mapping.get(status, status.title())


def _parse_datetime_string(value: str | None) -> str | None:
    if not value:
        return None

    try:
        cleaned = value.strip()
        if cleaned.endswith('Z'):
            cleaned = f'{cleaned[:-1]}+00:00'
        # Normalize duplicated timezone suffixes like +00:00+00:00
        if '+00:00+00:00' in cleaned:
            cleaned = cleaned.replace('+00:00+00:00', '+00:00')

        datetime.fromisoformat(cleaned)
        return cleaned
    except Exception:  # pragma: no cover - defensive
        return value


async def _resolve_connected_servers(
    db: AsyncSession,
    squad_uuids: list[str],
) -> list[MiniAppConnectedServer]:
    from app.services.metered_traffic_policy import get_customer_squad_uuids

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


async def _load_devices_info(user: User) -> tuple[int, list[MiniAppDevice]]:
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
                last_seen=_parse_datetime_string(last_seen_raw),
                last_ip=last_ip,
            )
        )

    if total_devices == 0:
        total_devices = len(devices)

    return total_devices, devices


def _resolve_display_name(user_data: dict[str, Any]) -> str:
    username = user_data.get('username')
    if username:
        return username

    first = user_data.get('first_name')
    last = user_data.get('last_name')
    parts = [part for part in [first, last] if part]
    if parts:
        return ' '.join(parts)

    telegram_id = user_data.get('telegram_id')
    return f'User {telegram_id}' if telegram_id else 'User'


def _is_remnawave_configured() -> bool:
    params = settings.get_remnawave_auth_params()
    return bool(params.get('base_url') and params.get('api_key'))


def _serialize_transaction(transaction: Transaction) -> MiniAppTransaction:
    return MiniAppTransaction(
        id=transaction.id,
        type=transaction.type,
        amount_kopeks=transaction.amount_kopeks,
        amount_rubles=round(transaction.amount_kopeks / 100, 2),
        description=transaction.description,
        payment_method=transaction.payment_method,
        external_id=transaction.external_id,
        is_completed=transaction.is_completed,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
    )


async def _load_subscription_links(
    subscription: Subscription,
) -> dict[str, Any]:
    if not subscription.remnawave_short_uuid or not _is_remnawave_configured():
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


async def _build_referral_info(
    db: AsyncSession,
    user: User,
) -> MiniAppReferralInfo | None:
    referral_code = getattr(user, 'referral_code', None)
    referral_settings = settings.get_referral_settings() or {}

    referral_link = None
    if referral_code:
        referral_link = settings.get_referral_link(referral_code)

    minimum_topup_kopeks = int(referral_settings.get('minimum_topup_kopeks') or 0)
    first_topup_bonus_kopeks = int(referral_settings.get('first_topup_bonus_kopeks') or 0)
    first_topup_bonus_days = int(referral_settings.get('first_topup_bonus_days') or 0)
    inviter_bonus_kopeks = int(referral_settings.get('inviter_bonus_kopeks') or 0)
    inviter_bonus_days = int(referral_settings.get('inviter_bonus_days') or 0)
    commission_percent = float(
        get_effective_referral_commission_percent(user) if user else referral_settings.get('commission_percent') or 0
    )

    terms = MiniAppReferralTerms(
        minimum_topup_kopeks=minimum_topup_kopeks,
        minimum_topup_label=settings.format_price(minimum_topup_kopeks),
        first_topup_bonus_kopeks=first_topup_bonus_kopeks,
        first_topup_bonus_label=settings.format_price(first_topup_bonus_kopeks),
        first_topup_bonus_days=first_topup_bonus_days,
        first_topup_bonus_days_label=f'{first_topup_bonus_days} дн.' if first_topup_bonus_days > 0 else None,
        inviter_bonus_kopeks=inviter_bonus_kopeks,
        inviter_bonus_label=settings.format_price(inviter_bonus_kopeks),
        inviter_bonus_days=inviter_bonus_days,
        inviter_bonus_days_label=f'{inviter_bonus_days} дн.' if inviter_bonus_days > 0 else None,
        commission_percent=commission_percent,
    )

    summary = await get_user_referral_summary(db, user.id)
    stats: MiniAppReferralStats | None = None
    recent_earnings: list[MiniAppReferralRecentEarning] = []

    if summary:
        total_earned_kopeks = int(summary.get('total_earned_kopeks') or 0)
        month_earned_kopeks = int(summary.get('month_earned_kopeks') or 0)

        stats = MiniAppReferralStats(
            invited_count=int(summary.get('invited_count') or 0),
            paid_referrals_count=int(summary.get('paid_referrals_count') or 0),
            active_referrals_count=int(summary.get('active_referrals_count') or 0),
            total_earned_kopeks=total_earned_kopeks,
            total_earned_label=settings.format_price(total_earned_kopeks),
            month_earned_kopeks=month_earned_kopeks,
            month_earned_label=settings.format_price(month_earned_kopeks),
            conversion_rate=float(summary.get('conversion_rate') or 0.0),
        )

        for earning in summary.get('recent_earnings', []) or []:
            amount = int(earning.get('amount_kopeks') or 0)
            recent_earnings.append(
                MiniAppReferralRecentEarning(
                    amount_kopeks=amount,
                    amount_label=settings.format_price(amount),
                    reason=earning.get('reason'),
                    referral_name=earning.get('referral_name'),
                    created_at=earning.get('created_at'),
                )
            )

    detailed = await get_detailed_referral_list(db, user.id, limit=50, offset=0)
    referral_items: list[MiniAppReferralItem] = []
    if detailed:
        for item in detailed.get('referrals', []) or []:
            total_earned = int(item.get('total_earned_kopeks') or 0)
            balance = int(item.get('balance_kopeks') or 0)
            referral_items.append(
                MiniAppReferralItem(
                    id=int(item.get('id') or 0),
                    telegram_id=item.get('telegram_id'),
                    full_name=item.get('full_name'),
                    username=item.get('username'),
                    created_at=item.get('created_at'),
                    last_activity=item.get('last_activity'),
                    has_made_first_topup=bool(item.get('has_made_first_topup')),
                    balance_kopeks=balance,
                    balance_label=settings.format_price(balance),
                    total_earned_kopeks=total_earned,
                    total_earned_label=settings.format_price(total_earned),
                    topups_count=int(item.get('topups_count') or 0),
                    days_since_registration=item.get('days_since_registration'),
                    days_since_activity=item.get('days_since_activity'),
                    status=item.get('status'),
                )
            )

    referral_list = MiniAppReferralList(
        total_count=int(detailed.get('total_count') or 0) if detailed else 0,
        has_next=bool(detailed.get('has_next')) if detailed else False,
        has_prev=bool(detailed.get('has_prev')) if detailed else False,
        current_page=int(detailed.get('current_page') or 1) if detailed else 1,
        total_pages=int(detailed.get('total_pages') or 1) if detailed else 1,
        items=referral_items,
    )

    if (
        not referral_code
        and not referral_link
        and not referral_items
        and not recent_earnings
        and (not stats or (stats.invited_count == 0 and stats.total_earned_kopeks == 0))
    ):
        return None

    return MiniAppReferralInfo(
        referral_code=referral_code,
        referral_link=referral_link,
        terms=terms,
        stats=stats,
        recent_earnings=recent_earnings,
        referrals=referral_list,
    )


def _is_trial_available_for_user(user: User) -> bool:
    if settings.TRIAL_DURATION_DAYS <= 0:
        return False

    if settings.is_trial_disabled_for_user(getattr(user, 'auth_type', 'telegram')):
        return False

    if getattr(user, 'has_had_paid_subscription', False):
        return False

    subscription = getattr(user, 'subscription', None)
    if subscription is not None:
        return False

    return True


@router.post('/subscription', response_model=MiniAppSubscriptionResponse)
async def get_subscription_details(
    payload: MiniAppSubscriptionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionResponse:
    # Check maintenance mode first
    if maintenance_service.is_maintenance_active():
        status_info = maintenance_service.get_status_info()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'code': 'maintenance',
                'message': maintenance_service.get_maintenance_message() or 'Service is under maintenance',
                'reason': status_info.get('reason'),
            },
        )

    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid Telegram user payload',
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid Telegram user identifier',
        ) from None

    # Check required channel subscription
    if settings.CHANNEL_IS_REQUIRED_SUB:
        from app.services.channel_subscription_service import channel_subscription_service

        channels_with_status = await channel_subscription_service.get_channels_with_status(telegram_id)
        is_subscribed = all(ch['is_subscribed'] for ch in channels_with_status) if channels_with_status else True

        if not is_subscribed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    'code': 'channel_subscription_required',
                    'message': 'Please subscribe to the required channels to continue',
                    'channels': channels_with_status,
                },
            )

    user = await get_user_by_telegram_id(db, telegram_id)
    purchase_url = (settings.MINIAPP_PURCHASE_URL or '').strip()

    if not user:
        detail: dict[str, Any] = {
            'code': 'user_not_found',
            'message': 'User not found. Please register in the bot to continue.',
            'title': 'Registration required',
        }
        if purchase_url:
            detail['purchase_url'] = purchase_url
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

    subscription = getattr(user, 'subscription', None)
    usage_synced = False

    if subscription and is_remnawave_configured():
        service = SubscriptionService()
        try:
            usage_synced = await service.sync_subscription_usage(db, subscription)
        except Exception as error:  # pragma: no cover - defensive logging
            logger.warning(
                'Failed to sync subscription usage for user', getattr=getattr(user, 'id', 'unknown'), error=error
            )

    if usage_synced:
        try:
            await db.refresh(subscription, attribute_names=['traffic_used_gb', 'updated_at'])
        except Exception as refresh_error:  # pragma: no cover - defensive logging
            logger.debug('Failed to refresh subscription after usage sync', refresh_error=refresh_error)

        try:
            await db.refresh(user)
        except Exception as refresh_error:  # pragma: no cover - defensive logging
            logger.debug('Failed to refresh user after usage sync', refresh_error=refresh_error)
            user = await get_user_by_telegram_id(db, telegram_id)

        subscription = getattr(user, 'subscription', subscription)
    lifetime_used = bytes_to_gb(getattr(user, 'lifetime_used_traffic_bytes', 0))

    transactions_query = (
        select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.created_at.desc()).limit(10)
    )
    transactions_result = await db.execute(transactions_query)
    transactions = list(transactions_result.scalars().all())

    balance_currency = getattr(user, 'balance_currency', None)
    if isinstance(balance_currency, str):
        balance_currency = balance_currency.upper()

    promo_group = getattr(user, 'promo_group', None)
    total_spent_kopeks = await get_user_total_spent_kopeks(db, user.id)
    auto_assign_groups = await get_auto_assign_promo_groups(db)

    auto_promo_levels: list[MiniAppAutoPromoGroupLevel] = []
    for group in auto_assign_groups:
        threshold = group.auto_assign_total_spent_kopeks or 0
        if threshold <= 0:
            continue

        auto_promo_levels.append(
            MiniAppAutoPromoGroupLevel(
                id=group.id,
                name=group.name,
                threshold_kopeks=threshold,
                threshold_rubles=round(threshold / 100, 2),
                threshold_label=settings.format_price(threshold),
                is_reached=total_spent_kopeks >= threshold,
                is_current=bool(promo_group and promo_group.id == group.id),
                **extract_promo_discounts(group),
            )
        )

    active_discount_percent = 0
    try:
        active_discount_percent = int(getattr(user, 'promo_offer_discount_percent', 0) or 0)
    except (TypeError, ValueError):
        active_discount_percent = 0

    active_discount_expires_at = getattr(user, 'promo_offer_discount_expires_at', None)
    now = datetime.now(UTC)
    if active_discount_expires_at and active_discount_expires_at <= now:
        active_discount_expires_at = None
        active_discount_percent = 0

    available_promo_offers = await list_active_discount_offers_for_user(db, user.id)

    promo_offer_source = getattr(user, 'promo_offer_discount_source', None)
    active_offer_contexts: list[ActiveOfferContext] = []
    if promo_offer_source or active_discount_percent > 0:
        active_discount_offer = await get_latest_claimed_offer_for_user(
            db,
            user.id,
            promo_offer_source,
        )
        if active_discount_offer and active_discount_percent > 0:
            active_offer_contexts.append(
                (
                    active_discount_offer,
                    active_discount_percent,
                    active_discount_expires_at,
                )
            )

    if subscription:
        active_offer_contexts.extend(await find_active_test_access_offers(db, subscription))

    promo_offers = await build_promo_offer_models(
        db,
        available_promo_offers,
        active_offer_contexts,
        user=user,
    )

    content_language_preference = user.language or settings.DEFAULT_LANGUAGE or 'ru'

    def _normalize_language_code(language: str | None) -> str:
        base_language = language or settings.DEFAULT_LANGUAGE or 'ru'
        return base_language.split('-')[0].lower()

    faq_payload: MiniAppFaq | None = None
    requested_faq_language = FaqService.normalize_language(content_language_preference)
    faq_pages = await FaqService.get_pages(
        db,
        requested_faq_language,
        include_inactive=False,
        fallback=True,
    )

    if faq_pages:
        faq_setting = await FaqService.get_setting(
            db,
            requested_faq_language,
            fallback=True,
        )
        is_enabled = bool(faq_setting.is_enabled) if faq_setting else True

        if is_enabled:
            ordered_pages = sorted(
                faq_pages,
                key=lambda page: (
                    (page.display_order or 0),
                    page.id,
                ),
            )
            faq_items: list[MiniAppFaqItem] = []
            for page in ordered_pages:
                raw_content = (page.content or '').strip()
                if not raw_content:
                    continue
                if not re.sub(r'<[^>]+>', '', raw_content).strip():
                    continue
                faq_items.append(
                    MiniAppFaqItem(
                        id=page.id,
                        title=page.title or None,
                        content=page.content or '',
                        display_order=getattr(page, 'display_order', None),
                    )
                )

            if faq_items:
                resolved_language = (
                    faq_setting.language if faq_setting and faq_setting.language else ordered_pages[0].language
                )
                faq_payload = MiniAppFaq(
                    requested_language=requested_faq_language,
                    language=resolved_language or requested_faq_language,
                    is_enabled=is_enabled,
                    total=len(faq_items),
                    items=faq_items,
                )

    legal_documents_payload: MiniAppLegalDocuments | None = None

    requested_offer_language = PublicOfferService.normalize_language(content_language_preference)
    public_offer = await PublicOfferService.get_active_offer(
        db,
        requested_offer_language,
    )
    if public_offer and (public_offer.content or '').strip():
        legal_documents_payload = legal_documents_payload or MiniAppLegalDocuments()
        legal_documents_payload.public_offer = MiniAppRichTextDocument(
            requested_language=requested_offer_language,
            language=public_offer.language,
            title=None,
            is_enabled=bool(public_offer.is_enabled),
            content=public_offer.content or '',
            created_at=public_offer.created_at,
            updated_at=public_offer.updated_at,
        )

    requested_policy_language = PrivacyPolicyService.normalize_language(content_language_preference)
    privacy_policy = await PrivacyPolicyService.get_active_policy(
        db,
        requested_policy_language,
    )
    if privacy_policy and (privacy_policy.content or '').strip():
        legal_documents_payload = legal_documents_payload or MiniAppLegalDocuments()
        legal_documents_payload.privacy_policy = MiniAppRichTextDocument(
            requested_language=requested_policy_language,
            language=privacy_policy.language,
            title=None,
            is_enabled=bool(privacy_policy.is_enabled),
            content=privacy_policy.content or '',
            created_at=privacy_policy.created_at,
            updated_at=privacy_policy.updated_at,
        )

    requested_rules_language = _normalize_language_code(content_language_preference)
    default_rules_language = _normalize_language_code(settings.DEFAULT_LANGUAGE)
    service_rules = await get_rules_by_language(db, requested_rules_language)
    if not service_rules and requested_rules_language != default_rules_language:
        service_rules = await get_rules_by_language(db, default_rules_language)

    if service_rules and (service_rules.content or '').strip():
        legal_documents_payload = legal_documents_payload or MiniAppLegalDocuments()
        legal_documents_payload.service_rules = MiniAppRichTextDocument(
            requested_language=requested_rules_language,
            language=service_rules.language,
            title=getattr(service_rules, 'title', None),
            is_enabled=bool(getattr(service_rules, 'is_active', True)),
            content=service_rules.content or '',
            created_at=getattr(service_rules, 'created_at', None),
            updated_at=getattr(service_rules, 'updated_at', None),
        )

    links_payload: dict[str, Any] = {}
    connected_squads: list[str] = []
    connected_servers: list[MiniAppConnectedServer] = []
    links: list[str] = []
    ss_conf_links: dict[str, str] = {}
    subscription_url: str | None = None
    subscription_crypto_link: str | None = None
    happ_redirect_link: str | None = None
    hide_subscription_link: bool = False
    remnawave_short_uuid: str | None = None
    status_actual = 'missing'
    subscription_status_value = 'none'
    traffic_used_value = 0.0
    traffic_limit_value = 0
    device_limit_value: int | None = settings.DEFAULT_DEVICE_LIMIT or None
    autopay_enabled = False

    if subscription:
        traffic_used_value = format_gb(subscription.traffic_used_gb)
        traffic_limit_value = subscription.traffic_limit_gb or 0
        status_actual = subscription.actual_status
        subscription_status_value = subscription.status
        links_payload = await load_subscription_links(subscription)
        # Флаг скрытия ссылки (скрывается только текст, кнопки работают)
        hide_subscription_link = settings.should_hide_subscription_link()
        subscription_url = links_payload.get('subscription_url') or subscription.subscription_url
        subscription_crypto_link = links_payload.get('happ_crypto_link') or subscription.subscription_crypto_link
        happ_redirect_link = get_happ_cryptolink_redirect_link(subscription_crypto_link)
        from app.services.metered_traffic_policy import get_customer_squad_uuids

        connected_squads = get_customer_squad_uuids(subscription.connected_squads)
        connected_servers = await resolve_connected_servers(db, connected_squads)
        links = links_payload.get('links') or connected_squads
        ss_conf_links = links_payload.get('ss_conf_links') or {}
        remnawave_short_uuid = subscription.remnawave_short_uuid
        device_limit_value = subscription.device_limit
        autopay_enabled = bool(subscription.autopay_enabled)

    autopay_payload = _build_autopay_payload(subscription)
    autopay_days_before = getattr(autopay_payload, 'autopay_days_before', None) if autopay_payload else None
    autopay_days_options = list(getattr(autopay_payload, 'autopay_days_options', []) or []) if autopay_payload else []
    autopay_extras = _autopay_response_extras(
        autopay_enabled,
        autopay_days_before,
        autopay_days_options,
        autopay_payload,
    )

    devices_count, devices = await load_devices_info(user)

    # Загружаем данные суточного тарифа
    is_daily_tariff = False
    is_daily_paused = False
    daily_tariff_name = None
    daily_price_kopeks = None
    daily_price_label = None
    daily_next_charge_at = None

    if subscription and getattr(subscription, 'tariff_id', None):
        tariff = await get_tariff_by_id(db, subscription.tariff_id)
        if tariff and getattr(tariff, 'is_daily', False):
            is_daily_tariff = True
            is_daily_paused = getattr(subscription, 'is_daily_paused', False)
            daily_tariff_name = tariff.name
            daily_price_kopeks = getattr(tariff, 'daily_price_kopeks', 0)
            daily_price_label = settings.format_price(daily_price_kopeks) + '/день' if daily_price_kopeks > 0 else None
            # Оставшееся время подписки (показываем даже при паузе)
            if subscription.end_date:
                daily_next_charge_at = subscription.end_date

    response_user = MiniAppSubscriptionUser(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=resolve_display_name(
            {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telegram_id': user.telegram_id,
            }
        ),
        language=user.language,
        status=user.status,
        subscription_status=subscription_status_value,
        subscription_actual_status=status_actual,
        status_label=status_label(status_actual),
        expires_at=getattr(subscription, 'end_date', None),
        device_limit=device_limit_value,
        traffic_used_gb=round(traffic_used_value, 2),
        traffic_used_label=format_gb_label(traffic_used_value),
        traffic_limit_gb=traffic_limit_value,
        traffic_limit_label=format_limit_label(traffic_limit_value),
        lifetime_used_traffic_gb=lifetime_used,
        has_active_subscription=status_actual in {'active', 'trial'},
        promo_offer_discount_percent=active_discount_percent,
        promo_offer_discount_expires_at=active_discount_expires_at,
        promo_offer_discount_source=promo_offer_source,
        is_daily_tariff=is_daily_tariff,
        is_daily_paused=is_daily_paused,
        daily_tariff_name=daily_tariff_name,
        daily_price_kopeks=daily_price_kopeks,
        daily_price_label=daily_price_label,
        daily_next_charge_at=daily_next_charge_at,
    )

    referral_info = await build_referral_info(db, user)

    trial_available = is_trial_available_for_user(user)
    trial_duration_days = settings.TRIAL_DURATION_DAYS if settings.TRIAL_DURATION_DAYS > 0 else None
    trial_price_kopeks = settings.get_trial_activation_price()
    trial_payment_required = settings.is_trial_paid_activation_enabled() and trial_price_kopeks > 0
    trial_price_label = settings.format_price(trial_price_kopeks) if trial_payment_required else None

    subscription_missing_reason = None
    if subscription is None:
        if not trial_available and settings.TRIAL_DURATION_DAYS > 0:
            subscription_missing_reason = 'trial_expired'
        else:
            subscription_missing_reason = 'not_found'

    # Получаем докупки трафика
    traffic_purchases_data = []
    if subscription:
        from sqlalchemy import select as sql_select

        from app.database.models import TrafficPurchase

        now = datetime.now(UTC)
        purchases_query = (
            sql_select(TrafficPurchase)
            .where(TrafficPurchase.subscription_id == subscription.id)
            .where(TrafficPurchase.expires_at > now)
            .order_by(TrafficPurchase.expires_at.asc())
        )
        purchases_result = await db.execute(purchases_query)
        purchases = purchases_result.scalars().all()

        for purchase in purchases:
            time_remaining = purchase.expires_at - now
            days_remaining = max(0, int(time_remaining.total_seconds() / 86400))
            total_duration_seconds = (purchase.expires_at - purchase.created_at).total_seconds()
            elapsed_seconds = (now - purchase.created_at).total_seconds()
            progress_percent = min(
                100.0, max(0.0, (elapsed_seconds / total_duration_seconds * 100) if total_duration_seconds > 0 else 0)
            )

            traffic_purchases_data.append(
                {
                    'id': purchase.id,
                    'traffic_gb': purchase.traffic_gb,
                    'expires_at': purchase.expires_at,
                    'created_at': purchase.created_at,
                    'days_remaining': days_remaining,
                    'progress_percent': round(progress_percent, 1),
                }
            )

    return MiniAppSubscriptionResponse(
        traffic_purchases=traffic_purchases_data,
        subscription_id=getattr(subscription, 'id', None),
        remnawave_short_uuid=remnawave_short_uuid,
        user=response_user,
        subscription_url=subscription_url,
        hide_subscription_link=hide_subscription_link,
        subscription_crypto_link=subscription_crypto_link,
        subscription_purchase_url=purchase_url or None,
        links=links,
        ss_conf_links=ss_conf_links,
        connected_squads=connected_squads,
        connected_servers=connected_servers,
        connected_devices_count=devices_count,
        connected_devices=devices,
        happ=links_payload.get('happ') if subscription else None,
        happ_link=links_payload.get('happ_link') if subscription else None,
        happ_crypto_link=subscription_crypto_link,  # Используем уже вычисленное значение с fallback
        happ_cryptolink_redirect_link=happ_redirect_link,
        happ_cryptolink_redirect_template=settings.get_happ_cryptolink_redirect_template(),
        balance_kopeks=user.balance_kopeks,
        balance_rubles=round(user.balance_rubles, 2),
        balance_currency=balance_currency,
        transactions=[serialize_transaction(tx) for tx in transactions],
        promo_offers=promo_offers,
        promo_group=(
            MiniAppPromoGroup(
                id=promo_group.id,
                name=promo_group.name,
                **extract_promo_discounts(promo_group),
            )
            if promo_group
            else None
        ),
        auto_assign_promo_groups=auto_promo_levels,
        total_spent_kopeks=total_spent_kopeks,
        total_spent_rubles=round(total_spent_kopeks / 100, 2),
        total_spent_label=settings.format_price(total_spent_kopeks),
        subscription_type=('trial' if subscription and subscription.is_trial else ('paid' if subscription else 'none')),
        autopay_enabled=autopay_enabled,
        autopay_days_before=autopay_days_before,
        autopay_days_options=autopay_days_options,
        autopay=autopay_payload,
        autopay_settings=autopay_payload,
        branding=settings.get_miniapp_branding(),
        faq=faq_payload,
        legal_documents=legal_documents_payload,
        referral=referral_info,
        subscription_missing=subscription is None,
        subscription_missing_reason=subscription_missing_reason,
        trial_available=trial_available,
        trial_duration_days=trial_duration_days,
        trial_status='available' if trial_available else 'unavailable',
        trial_payment_required=trial_payment_required,
        trial_price_kopeks=trial_price_kopeks if trial_payment_required else None,
        trial_price_label=trial_price_label,
        sales_mode=settings.get_sales_mode(),
        current_tariff=await get_current_tariff_model(db, subscription, user) if subscription else None,
        **autopay_extras,
    )


@router.post(
    '/subscription/autopay',
    response_model=MiniAppSubscriptionAutopayResponse,
)
async def update_subscription_autopay_endpoint(
    payload: MiniAppSubscriptionAutopayRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionAutopayResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(user)
    _validate_subscription_id(payload.subscription_id, subscription)

    # Суточные подписки имеют свой механизм продления (DailySubscriptionService),
    # глобальный autopay для них запрещён
    target_enabled = bool(payload.enabled) if payload.enabled is not None else bool(subscription.autopay_enabled)
    if target_enabled:
        try:
            await db.refresh(subscription, ['tariff'])
        except Exception:
            pass
        if subscription.tariff and getattr(subscription.tariff, 'is_daily', False):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'autopay_not_available_for_daily',
                    'message': 'Autopay is not available for daily subscriptions',
                },
            )

    requested_days = payload.days_before
    normalized_days = _normalize_autopay_days(requested_days)
    current_days = _normalize_autopay_days(getattr(subscription, 'autopay_days_before', None))
    if normalized_days is None:
        normalized_days = current_days

    options = _get_autopay_day_options(subscription)
    default_day = _normalize_autopay_days(getattr(settings, 'DEFAULT_AUTOPAY_DAYS_BEFORE', None))
    if default_day is None and options:
        default_day = options[0]

    if target_enabled and normalized_days is None:
        if default_day is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'autopay_no_days',
                    'message': 'Auto-pay day selection is temporarily unavailable',
                },
            )
        normalized_days = default_day

    if normalized_days is None:
        normalized_days = default_day or (options[0] if options else 1)

    if bool(subscription.autopay_enabled) == target_enabled and current_days == normalized_days:
        autopay_payload = _build_autopay_payload(subscription)
        autopay_days_before = getattr(autopay_payload, 'autopay_days_before', None) if autopay_payload else None
        autopay_days_options = (
            list(getattr(autopay_payload, 'autopay_days_options', []) or []) if autopay_payload else options
        )
        extras = _autopay_response_extras(
            target_enabled,
            autopay_days_before,
            autopay_days_options,
            autopay_payload,
        )
        return MiniAppSubscriptionAutopayResponse(
            subscription_id=subscription.id,
            autopay_enabled=target_enabled,
            autopay_days_before=autopay_days_before,
            autopay_days_options=autopay_days_options,
            autopay=autopay_payload,
            autopay_settings=autopay_payload,
            **extras,
        )

    updated_subscription = await update_subscription_autopay(
        db,
        subscription,
        target_enabled,
        normalized_days,
    )

    autopay_payload = _build_autopay_payload(updated_subscription)
    autopay_days_before = getattr(autopay_payload, 'autopay_days_before', None) if autopay_payload else None
    autopay_days_options = (
        list(getattr(autopay_payload, 'autopay_days_options', []) or [])
        if autopay_payload
        else _get_autopay_day_options(updated_subscription)
    )
    extras = _autopay_response_extras(
        bool(updated_subscription.autopay_enabled),
        autopay_days_before,
        autopay_days_options,
        autopay_payload,
    )

    return MiniAppSubscriptionAutopayResponse(
        subscription_id=updated_subscription.id,
        autopay_enabled=bool(updated_subscription.autopay_enabled),
        autopay_days_before=autopay_days_before,
        autopay_days_options=autopay_days_options,
        autopay=autopay_payload,
        autopay_settings=autopay_payload,
        **extras,
    )


@router.post(
    '/subscription/trial',
    response_model=MiniAppSubscriptionTrialResponse,
)
async def activate_subscription_trial_endpoint(
    payload: MiniAppSubscriptionTrialRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionTrialResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)

    existing_subscription = getattr(user, 'subscription', None)
    if existing_subscription is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'subscription_exists',
                'message': 'Subscription is already active',
            },
        )

    if not is_trial_available_for_user(user):
        error_code = 'trial_unavailable'
        if getattr(user, 'has_had_paid_subscription', False):
            error_code = 'trial_expired'
        elif settings.TRIAL_DURATION_DAYS <= 0:
            error_code = 'trial_disabled'
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': error_code,
                'message': 'Trial is not available for this user',
            },
        )

    try:
        preview_trial_activation_charge(user)
    except TrialPaymentInsufficientFunds as error:
        missing = error.missing_amount
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': 'Not enough funds to activate the trial',
                'missing_amount_kopeks': missing,
                'required_amount_kopeks': error.required_amount,
                'balance_kopeks': error.balance_amount,
            },
        ) from error
    forced_devices = None
    if not settings.is_devices_selection_enabled():
        forced_devices = settings.get_disabled_mode_device_limit()

    trial_parameters = await resolve_trial_parameters(db, device_limit_override=forced_devices)

    try:
        subscription = await create_trial_subscription(
            db,
            user.id,
            duration_days=trial_parameters.duration_days,
            device_limit=trial_parameters.device_limit,
            traffic_limit_gb=trial_parameters.traffic_limit_gb,
            connected_squads=trial_parameters.connected_squads,
            tariff_id=trial_parameters.tariff_id,
        )
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error('Failed to activate trial subscription for user', user_id=user.id, error=error)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'code': 'trial_activation_failed',
                'message': 'Failed to activate trial subscription',
            },
        ) from error

    charged_amount = 0
    try:
        charged_amount = await charge_trial_activation_if_required(db, user)
    except TrialPaymentInsufficientFunds as error:
        rollback_success = await rollback_trial_subscription_activation(db, subscription)
        await db.refresh(user)
        if not rollback_success:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after charge error',
                },
            ) from error

        logger.error('Balance check failed after trial creation for user', user_id=user.id, error=error)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': 'Not enough funds to activate the trial',
                'missing_amount_kopeks': error.missing_amount,
                'required_amount_kopeks': error.required_amount,
                'balance_kopeks': error.balance_amount,
            },
        ) from error
    except TrialPaymentChargeFailed as error:
        rollback_success = await rollback_trial_subscription_activation(db, subscription)
        await db.refresh(user)
        if not rollback_success:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after charge error',
                },
            ) from error

        logger.error(
            'Failed to charge balance for trial activation after subscription creation',
            subscription_id=subscription.id,
            error=error,
        )
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'code': 'charge_failed',
                'message': 'Failed to charge balance for trial activation',
            },
        ) from error

    await db.refresh(user)
    await db.refresh(subscription)

    subscription_service = SubscriptionService()
    try:
        await subscription_service.create_remnawave_user(db, subscription)
    except RemnaWaveConfigurationError as error:  # pragma: no cover - configuration issues
        logger.error('RemnaWave update skipped due to configuration error', error=error)
        revert_result = await revert_trial_activation(
            db,
            user,
            subscription,
            charged_amount,
            refund_description='Возврат оплаты за активацию триала в мини-приложении',
        )
        if not revert_result.subscription_rolled_back:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after RemnaWave error',
                },
            ) from error
        if charged_amount > 0 and not revert_result.refunded:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_refund_failed',
                    'message': 'Failed to refund trial activation charge after RemnaWave error',
                },
            ) from error

        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'remnawave_configuration_error',
                'message': 'Trial activation failed due to RemnaWave configuration. Charge refunded.',
            },
        ) from error
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error(
            'Failed to create RemnaWave user for trial subscription', subscription_id=subscription.id, error=error
        )
        revert_result = await revert_trial_activation(
            db,
            user,
            subscription,
            charged_amount,
            refund_description='Возврат оплаты за активацию триала в мини-приложении',
        )
        if not revert_result.subscription_rolled_back:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after RemnaWave error',
                },
            ) from error
        if charged_amount > 0 and not revert_result.refunded:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_refund_failed',
                    'message': 'Failed to refund trial activation charge after RemnaWave error',
                },
            ) from error

        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'remnawave_provisioning_failed',
                'message': 'Trial activation failed due to RemnaWave provisioning. Charge refunded.',
            },
        ) from error

    await db.refresh(subscription)

    duration_days: int | None = None
    if subscription.start_date and subscription.end_date:
        try:
            duration_days = max(
                0,
                (subscription.end_date.date() - subscription.start_date.date()).days,
            )
        except Exception:  # pragma: no cover - defensive fallback
            duration_days = None

    if not duration_days and settings.TRIAL_DURATION_DAYS > 0:
        duration_days = settings.TRIAL_DURATION_DAYS

    language_code = _normalize_language_code(user)
    charged_amount_label = settings.format_price(charged_amount) if charged_amount > 0 else None
    if language_code in {'ru', 'fa'}:
        if duration_days:
            message = f'Триал активирован на {duration_days} дн. Приятного пользования!'
        else:
            message = 'Триал активирован. Приятного пользования!'
    elif duration_days:
        message = f'Trial activated for {duration_days} days. Enjoy!'
    else:
        message = 'Trial activated successfully. Enjoy!'

    if charged_amount_label:
        if language_code in {'ru', 'fa'}:
            message = f'{message}\n\n💳 С вашего баланса списано {charged_amount_label}.'
        else:
            message = f'{message}\n\n💳 {charged_amount_label} has been deducted from your balance.'

    await with_admin_notification_service(
        lambda service: service.send_trial_activation_notification(
            db,
            user,
            subscription,
            charged_amount_kopeks=charged_amount,
        )
    )

    return MiniAppSubscriptionTrialResponse(
        message=message,
        subscription_id=getattr(subscription, 'id', None),
        trial_status='activated',
        trial_duration_days=duration_days,
        charged_amount_kopeks=charged_amount if charged_amount > 0 else None,
        charged_amount_label=charged_amount_label,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )


@router.post(
    '/promo-codes/activate',
    response_model=MiniAppPromoCodeActivationResponse,
)
async def activate_promo_code(
    payload: MiniAppPromoCodeActivationRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPromoCodeActivationResponse:
    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    code = (payload.code or '').strip().upper()
    if not code:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid', 'message': 'Promo code must not be empty'},
        )

    result = await promo_code_service.activate_promocode(db, user.id, code)
    if result.get('success'):
        promocode_data = result.get('promocode') or {}

        try:
            balance_bonus = int(promocode_data.get('balance_bonus_kopeks') or 0)
        except (TypeError, ValueError):
            balance_bonus = 0

        try:
            subscription_days = int(promocode_data.get('subscription_days') or 0)
        except (TypeError, ValueError):
            subscription_days = 0

        promo_payload = MiniAppPromoCode(
            code=str(promocode_data.get('code') or code),
            type=promocode_data.get('type'),
            balance_bonus_kopeks=balance_bonus,
            subscription_days=subscription_days,
            max_uses=promocode_data.get('max_uses'),
            current_uses=promocode_data.get('current_uses'),
            valid_until=promocode_data.get('valid_until'),
        )

        return MiniAppPromoCodeActivationResponse(
            success=True,
            description=result.get('description'),
            promocode=promo_payload,
        )

    error_code = str(result.get('error') or 'generic')
    status_map = {
        'user_not_found': status.HTTP_404_NOT_FOUND,
        'not_found': status.HTTP_404_NOT_FOUND,
        'expired': status.HTTP_410_GONE,
        'used': status.HTTP_409_CONFLICT,
        'already_used_by_user': status.HTTP_409_CONFLICT,
        'no_subscription_for_days': status.HTTP_400_BAD_REQUEST,
        'active_discount_exists': status.HTTP_409_CONFLICT,
        'not_first_purchase': status.HTTP_400_BAD_REQUEST,
        'daily_limit': status.HTTP_429_TOO_MANY_REQUESTS,
        'server_error': status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    message_map = {
        'invalid': 'Promo code must not be empty',
        'not_found': 'Promo code not found',
        'expired': 'Promo code expired',
        'used': 'Promo code already used',
        'already_used_by_user': 'Promo code already used by this user',
        'no_subscription_for_days': 'This promo code requires an active or expired subscription',
        'active_discount_exists': 'You already have an active discount',
        'not_first_purchase': 'This promo code is only available for first purchase',
        'daily_limit': 'Too many promo code activations today',
        'user_not_found': 'User not found',
        'server_error': 'Failed to activate promo code',
    }

    http_status = status_map.get(error_code, status.HTTP_400_BAD_REQUEST)
    message = message_map.get(error_code, 'Unable to activate promo code')

    raise HTTPException(
        http_status,
        detail={'code': error_code, 'message': message},
    )


@router.post(
    '/promo-offers/{offer_id}/claim',
    response_model=MiniAppPromoOfferClaimResponse,
)
async def claim_promo_offer(
    offer_id: int,
    payload: MiniAppPromoOfferClaimRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPromoOfferClaimResponse:
    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    offer = await get_offer_by_id(db, offer_id)
    if not offer or offer.user_id != user.id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'offer_not_found', 'message': 'Offer not found'},
        )

    now = datetime.now(UTC)
    if offer.claimed_at is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={'code': 'already_claimed', 'message': 'Offer already claimed'},
        )

    if not offer.is_active or offer.expires_at <= now:
        offer.is_active = False
        await db.commit()
        raise HTTPException(
            status.HTTP_410_GONE,
            detail={'code': 'offer_expired', 'message': 'Offer expired'},
        )

    effect_type = normalize_effect_type(getattr(offer, 'effect_type', None))

    if effect_type == 'test_access':
        success, newly_added, expires_at, error_code = await promo_offer_service.grant_test_access(
            db,
            user,
            offer,
        )

        if not success:
            code = error_code or 'claim_failed'
            message_map = {
                'subscription_missing': 'Active subscription required',
                'squads_missing': 'No squads configured for test access',
                'already_connected': 'Servers already connected',
                'remnawave_sync_failed': 'Failed to apply servers',
            }
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={'code': code, 'message': message_map.get(code, 'Unable to activate offer')},
            )

        await mark_offer_claimed(
            db,
            offer,
            details={
                'context': 'test_access_claim',
                'new_squads': newly_added,
                'expires_at': expires_at.isoformat() if expires_at else None,
            },
        )

        return MiniAppPromoOfferClaimResponse(success=True, code='test_access_claimed')

    discount_percent = int(getattr(offer, 'discount_percent', 0) or 0)
    if discount_percent <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_discount', 'message': 'Offer does not contain discount'},
        )

    user.promo_offer_discount_percent = discount_percent
    user.promo_offer_discount_source = offer.notification_type
    user.updated_at = now

    extra_data = extract_offer_extra(offer)
    raw_duration = extra_data.get('active_discount_hours')
    template_id = extra_data.get('template_id')

    if raw_duration in (None, '') and template_id:
        try:
            template = await get_promo_offer_template_by_id(db, int(template_id))
        except (TypeError, ValueError):
            template = None
        if template and template.active_discount_hours:
            raw_duration = template.active_discount_hours
    else:
        template = None

    try:
        duration_hours = int(raw_duration) if raw_duration is not None else None
    except (TypeError, ValueError):
        duration_hours = None

    if duration_hours and duration_hours > 0:
        discount_expires_at = now + timedelta(hours=duration_hours)
    else:
        discount_expires_at = None

    user.promo_offer_discount_expires_at = discount_expires_at

    await mark_offer_claimed(
        db,
        offer,
        details={
            'context': 'discount_claim',
            'discount_percent': discount_percent,
            'discount_expires_at': discount_expires_at.isoformat() if discount_expires_at else None,
        },
    )
    await db.refresh(user)

    return MiniAppPromoOfferClaimResponse(success=True, code='discount_claimed')


@router.post(
    '/devices/remove',
    response_model=MiniAppDeviceRemovalResponse,
)
async def remove_connected_device(
    payload: MiniAppDeviceRemovalRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppDeviceRemovalResponse:
    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    remnawave_uuid = getattr(user, 'remnawave_uuid', None)
    if not remnawave_uuid:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={'code': 'remnawave_unavailable', 'message': 'RemnaWave user is not linked'},
        )

    hwid = (payload.hwid or '').strip()
    if not hwid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_hwid', 'message': 'Device identifier is required'},
        )

    service = RemnaWaveService()
    if not service.is_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'code': 'service_unavailable', 'message': 'Device management is temporarily unavailable'},
        )

    try:
        async with service.get_api_client() as api:
            success = await api.remove_device(remnawave_uuid, hwid)
    except RemnaWaveConfigurationError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'code': 'service_unavailable', 'message': str(error)},
        ) from error
    except Exception as error:  # pragma: no cover - defensive
        logger.warning('Failed to remove device for user', hwid=hwid, telegram_id=telegram_id, error=error)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={'code': 'remnawave_error', 'message': 'Failed to remove device'},
        ) from error

    if not success:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={'code': 'remnawave_error', 'message': 'Failed to remove device'},
        )

    return MiniAppDeviceRemovalResponse(success=True)


@router.post(
    '/subscription/renewal/options',
    response_model=MiniAppSubscriptionRenewalOptionsResponse,
)
async def get_subscription_renewal_options_endpoint(
    payload: MiniAppSubscriptionRenewalOptionsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionRenewalOptionsResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial', 'expired'},
    )
    _validate_subscription_id(payload.subscription_id, subscription)

    periods, pricing_map, default_period_id = await prepare_subscription_renewal_options(
        db,
        user,
        subscription,
        renewal_service=renewal_service,
        logger=logger,
    )

    balance_kopeks = getattr(user, 'balance_kopeks', 0)
    currency = (getattr(user, 'balance_currency', None) or 'RUB').upper()

    promo_group = getattr(user, 'promo_group', None)
    promo_group_model = (
        MiniAppPromoGroup(
            id=promo_group.id,
            name=promo_group.name,
            **extract_promo_discounts(promo_group),
        )
        if promo_group
        else None
    )

    promo_offer_payload = build_promo_offer_payload(user)

    missing_amount = None
    if default_period_id and default_period_id in pricing_map:
        selected_pricing = pricing_map[default_period_id]
        final_total = selected_pricing.get('final_total')
        if isinstance(final_total, int) and balance_kopeks < final_total:
            missing_amount = final_total - balance_kopeks

    renewal_autopay_payload = _build_autopay_payload(subscription)
    renewal_autopay_days_before = (
        getattr(renewal_autopay_payload, 'autopay_days_before', None) if renewal_autopay_payload else None
    )
    renewal_autopay_days_options = (
        list(getattr(renewal_autopay_payload, 'autopay_days_options', []) or []) if renewal_autopay_payload else []
    )
    renewal_autopay_extras = _autopay_response_extras(
        bool(subscription.autopay_enabled),
        renewal_autopay_days_before,
        renewal_autopay_days_options,
        renewal_autopay_payload,
    )

    return MiniAppSubscriptionRenewalOptionsResponse(
        subscription_id=subscription.id,
        currency=currency,
        balance_kopeks=balance_kopeks,
        balance_label=settings.format_price(balance_kopeks),
        promo_group=promo_group_model,
        promo_offer=promo_offer_payload,
        periods=periods,
        default_period_id=default_period_id,
        missing_amount_kopeks=missing_amount,
        status_message=build_renewal_status_message(user),
        autopay_enabled=bool(subscription.autopay_enabled),
        autopay_days_before=renewal_autopay_days_before,
        autopay_days_options=renewal_autopay_days_options,
        autopay=renewal_autopay_payload,
        autopay_settings=renewal_autopay_payload,
        is_trial=bool(getattr(subscription, 'is_trial', False)),
        sales_mode=settings.get_sales_mode(),
        **renewal_autopay_extras,
    )


@router.post(
    '/subscription/renewal',
    response_model=MiniAppSubscriptionRenewalResponse,
)
async def submit_subscription_renewal_endpoint(
    payload: MiniAppSubscriptionRenewalRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionRenewalResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial', 'expired'},
    )
    _validate_subscription_id(payload.subscription_id, subscription)

    period_days = resolve_renewal_period(payload.period_days, payload.period_id)
    tariff_pricing = await build_tariff_renewal_pricing(
        db,
        user,
        subscription,
        period_days,
    )
    if not tariff_pricing:
        ensure_classic_renewal_period_available(period_days)
    method = resolve_renewal_method(payload.method)

    pricing_model = None
    if tariff_pricing:
        final_total = tariff_pricing['final_total']
        pricing = tariff_pricing
    else:
        try:
            pricing_model = await _calculate_subscription_renewal_pricing(
                db,
                user,
                subscription,
                period_days,
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.error(
                'Failed to calculate renewal pricing for subscription (period)',
                subscription_id=subscription.id,
                period_days=period_days,
                error=error,
            )
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail={'code': 'pricing_failed', 'message': 'Failed to calculate renewal pricing'},
            ) from error

        final_total = pricing_model.final_total
        pricing = pricing_model.to_payload()

    balance_kopeks = getattr(user, 'balance_kopeks', 0)
    missing_amount = calculate_missing_amount(balance_kopeks, final_total)
    description = f'Продление подписки на {period_days} дней'

    if missing_amount <= 0:
        if tariff_pricing:
            updated_subscription = await execute_tariff_renewal(
                db,
                user,
                subscription,
                period_days=period_days,
                final_total=final_total,
                description=description,
                logger=logger,
            )
            new_end_date = updated_subscription.end_date
            lang = getattr(user, 'language', settings.DEFAULT_LANGUAGE)
            if lang == 'ru':
                message = f'Подписка продлена до {new_end_date.strftime("%d.%m.%Y")}'
            else:
                message = f'Subscription extended until {new_end_date.strftime("%Y-%m-%d")}'

            return MiniAppSubscriptionRenewalResponse(
                message=message,
                balance_kopeks=user.balance_kopeks,
                balance_label=settings.format_price(user.balance_kopeks),
                subscription_id=updated_subscription.id,
                renewed_until=new_end_date,
            )

        if pricing_model is None:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'code': 'pricing_missing', 'message': 'Failed to calculate renewal pricing'},
            )
        result = await execute_classic_renewal(
            db,
            renewal_service,
            user,
            subscription,
            pricing_model,
            description=description,
            logger=logger,
        )

        updated_subscription = result.subscription
        message = build_renewal_success_message(
            user,
            updated_subscription,
            result.total_amount_kopeks,
            pricing_model.promo_discount_value,
        )

        return MiniAppSubscriptionRenewalResponse(
            message=message,
            balance_kopeks=user.balance_kopeks,
            balance_label=settings.format_price(user.balance_kopeks),
            subscription_id=updated_subscription.id,
            renewed_until=updated_subscription.end_date,
        )

    supported_methods = {'cryptobot'}
    ensure_renewal_method_or_balance(
        method=method,
        final_total=final_total,
        balance_kopeks=balance_kopeks,
    )
    ensure_renewal_method_supported(method, supported_methods)

    if method == 'cryptobot':
        payment_data = await create_renewal_cryptobot_payment(
            db=db,
            user=user,
            subscription=subscription,
            period_days=period_days,
            final_total=final_total,
            missing_amount=missing_amount,
            description=description,
            pricing_snapshot=pricing,
            rate_resolver=_get_usd_to_rub_rate,
            limits_calculator=_compute_cryptobot_limits,
            payment_service_factory=PaymentService,
        )

        message = build_renewal_pending_message(user, missing_amount, method)

        return MiniAppSubscriptionRenewalResponse(
            success=False,
            message=message,
            balance_kopeks=user.balance_kopeks,
            balance_label=settings.format_price(user.balance_kopeks),
            subscription_id=subscription.id,
            requires_payment=True,
            payment_method=method,
            payment_url=payment_data['payment_url'],
            payment_amount_kopeks=missing_amount,
            payment_id=payment_data['payment_id'],
            invoice_id=payment_data['invoice_id'],
            payment_payload=payment_data['payment_payload'],
            payment_extra=payment_data['payment_extra'],
        )

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail={'code': 'unsupported_method', 'message': 'Payment method is not supported for renewal'},
    )


@router.post(
    '/subscription/purchase/options',
    response_model=MiniAppSubscriptionPurchaseOptionsResponse,
)
async def get_subscription_purchase_options_endpoint(
    payload: MiniAppSubscriptionPurchaseOptionsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionPurchaseOptionsResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    context = await purchase_service.build_options(db, user)

    data_payload = dict(context.payload)
    data_payload.setdefault('currency', context.currency)
    data_payload.setdefault('balance_kopeks', context.balance_kopeks)
    data_payload.setdefault('balanceKopeks', context.balance_kopeks)
    data_payload.setdefault('balance_label', settings.format_price(context.balance_kopeks))
    data_payload.setdefault('balanceLabel', settings.format_price(context.balance_kopeks))

    return MiniAppSubscriptionPurchaseOptionsResponse(
        currency=context.currency,
        balance_kopeks=context.balance_kopeks,
        balance_label=settings.format_price(context.balance_kopeks),
        subscription_id=data_payload.get('subscription_id') or data_payload.get('subscriptionId'),
        data=data_payload,
    )


@router.post(
    '/subscription/purchase/preview',
    response_model=MiniAppSubscriptionPurchasePreviewResponse,
)
async def subscription_purchase_preview_endpoint(
    payload: MiniAppSubscriptionPurchasePreviewRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionPurchasePreviewResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    context = await purchase_service.build_options(db, user)

    selection_payload = merge_purchase_selection_from_request(payload)
    try:
        selection = purchase_service.parse_selection(context, selection_payload)
    except PurchaseValidationError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': error.code, 'message': str(error)},
        ) from error

    pricing = await purchase_service.calculate_pricing(db, context, selection)
    preview_payload = purchase_service.build_preview_payload(context, pricing)

    balance_label = settings.format_price(getattr(user, 'balance_kopeks', 0))

    return MiniAppSubscriptionPurchasePreviewResponse(
        preview=preview_payload,
        balance_kopeks=user.balance_kopeks,
        balance_label=balance_label,
    )


@router.post(
    '/subscription/purchase',
    response_model=MiniAppSubscriptionPurchaseResponse,
)
async def subscription_purchase_endpoint(
    payload: MiniAppSubscriptionPurchaseRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionPurchaseResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    context = await purchase_service.build_options(db, user)

    selection_payload = merge_purchase_selection_from_request(payload)
    try:
        selection = purchase_service.parse_selection(context, selection_payload)
    except PurchaseValidationError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': error.code, 'message': str(error)},
        ) from error

    pricing = await purchase_service.calculate_pricing(db, context, selection)

    try:
        result = await purchase_service.submit_purchase(db, context, pricing)
    except PurchaseBalanceError as error:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={'code': 'insufficient_funds', 'message': str(error)},
        ) from error
    except PurchaseValidationError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': error.code, 'message': str(error)},
        ) from error

    await db.refresh(user)

    subscription = result.get('subscription')
    transaction = result.get('transaction')
    was_trial_conversion = bool(result.get('was_trial_conversion'))
    period_days = getattr(getattr(pricing, 'selection', None), 'period', None)
    period_days = getattr(period_days, 'days', None) if period_days else None

    if subscription is not None:
        try:
            await db.refresh(subscription)
        except Exception:  # pragma: no cover - defensive refresh safeguard
            pass

    if subscription and transaction and period_days:
        await with_admin_notification_service(
            lambda service: service.send_subscription_purchase_notification(
                db,
                user,
                subscription,
                transaction,
                period_days,
                was_trial_conversion=was_trial_conversion,
            )
        )

    balance_label = settings.format_price(getattr(user, 'balance_kopeks', 0))

    return MiniAppSubscriptionPurchaseResponse(
        message=result.get('message'),
        balance_kopeks=user.balance_kopeks,
        balance_label=balance_label,
        subscription_id=getattr(subscription, 'id', None),
    )


@router.post(
    '/subscription/settings',
    response_model=MiniAppSubscriptionSettingsResponse,
)
async def get_subscription_settings_endpoint(
    payload: MiniAppSubscriptionSettingsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionSettingsResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    _validate_subscription_id(payload.subscription_id, subscription)

    settings_payload = await build_subscription_settings(db, user, subscription)

    return MiniAppSubscriptionSettingsResponse(settings=settings_payload)


@router.post(
    '/subscription/servers',
    response_model=MiniAppSubscriptionUpdateResponse,
)
async def update_subscription_servers_endpoint(
    payload: MiniAppSubscriptionServersUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionUpdateResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    _validate_subscription_id(payload.subscription_id, subscription)
    old_servers = list(getattr(subscription, 'connected_squads', []) or [])

    selected_order = resolve_selected_server_order(payload)
    _, added, removed = resolve_server_changes(subscription, selected_order)

    if not added and not removed:
        return MiniAppSubscriptionUpdateResponse(
            success=True,
            message='No changes',
        )

    plan = await build_servers_update_plan(
        db,
        user,
        subscription,
        selected_order=selected_order,
        added=added,
        removed=removed,
    )
    total_cost = int(plan['total_cost'])
    await apply_servers_update_plan(
        db,
        user,
        subscription,
        selected_order=selected_order,
        added=added,
        total_cost=total_cost,
        charged_months=int(plan['charged_months']),
        catalog=plan['catalog'],
        added_server_ids=plan['added_server_ids'],
        added_server_prices=plan['added_server_prices'],
        removed_server_ids=plan['removed_server_ids'],
        logger=logger,
    )
    await finalize_subscription_update(
        db,
        user,
        subscription,
        change_type='servers',
        old_value=old_servers,
        new_value=subscription.connected_squads or [],
        price_paid=max(total_cost, 0),
        with_admin_notification_service=with_admin_notification_service,
    )

    return MiniAppSubscriptionUpdateResponse(success=True)


@router.post(
    '/subscription/traffic',
    response_model=MiniAppSubscriptionUpdateResponse,
)
async def update_subscription_traffic_endpoint(
    payload: MiniAppSubscriptionTrafficUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionUpdateResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    _validate_subscription_id(payload.subscription_id, subscription)
    old_traffic = subscription.traffic_limit_gb

    new_traffic = resolve_new_traffic_value(payload)

    if new_traffic == subscription.traffic_limit_gb:
        return MiniAppSubscriptionUpdateResponse(success=True, message='No changes')

    ensure_traffic_update_allowed(new_traffic)
    total_price_difference, months_remaining = calculate_traffic_upgrade_cost(
        user,
        subscription,
        new_traffic,
    )
    await charge_traffic_upgrade(
        db,
        user,
        subscription,
        new_traffic=new_traffic,
        total_price_difference=total_price_difference,
        months_remaining=months_remaining,
    )

    subscription.traffic_limit_gb = new_traffic
    await finalize_subscription_update(
        db,
        user,
        subscription,
        change_type='traffic',
        old_value=old_traffic,
        new_value=subscription.traffic_limit_gb,
        price_paid=max(total_price_difference, 0),
        with_admin_notification_service=with_admin_notification_service,
    )

    return MiniAppSubscriptionUpdateResponse(success=True)


@router.post(
    '/subscription/devices',
    response_model=MiniAppSubscriptionUpdateResponse,
)
async def update_subscription_devices_endpoint(
    payload: MiniAppSubscriptionDevicesUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionUpdateResponse:
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    _validate_subscription_id(payload.subscription_id, subscription)

    # Re-read subscription under row lock to prevent concurrent device purchases exceeding limit
    locked_result = await db.execute(
        select(Subscription)
        .where(Subscription.id == subscription.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    subscription = locked_result.scalar_one()
    current_devices, new_devices = resolve_device_limits(payload, subscription)
    old_devices = current_devices

    if new_devices == current_devices:
        return MiniAppSubscriptionUpdateResponse(success=True, message='No changes')

    price_to_charge, charged_months = calculate_devices_upgrade_cost(
        user,
        subscription,
        current_devices=current_devices,
        new_devices=new_devices,
    )
    await charge_devices_upgrade(
        db,
        user,
        current_devices=current_devices,
        new_devices=new_devices,
        price_to_charge=price_to_charge,
        charged_months=charged_months,
        subscription_end_date=subscription.end_date,
    )

    if price_to_charge > 0:
        # Re-lock subscription after subtract_user_balance committed (which released all locks).
        # Re-validate to prevent concurrent device purchases from exceeding the limit or double-charging.
        relock_result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        subscription = relock_result.scalar_one()

        actual_current = subscription.device_limit or 1
        actual_delta = new_devices - actual_current
        max_devices_limit = settings.MAX_DEVICES_LIMIT

        if actual_delta <= 0 or (max_devices_limit > 0 and new_devices > max_devices_limit):
            # Concurrent request already applied the change or pushed limit beyond max — refund
            user_refund = await db.execute(
                select(User).where(User.id == user.id).with_for_update().execution_options(populate_existing=True)
            )
            refund_user = user_refund.scalar_one()
            refund_user.balance_kopeks += price_to_charge
            await db.commit()
            if actual_delta <= 0:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail={
                        'code': 'already_applied',
                        'message': 'Изменение уже применено параллельным запросом. Баланс возвращён.',
                    },
                )
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail={
                    'code': 'devices_limit_exceeded',
                    'message': f'Превышен максимальный лимит устройств ({max_devices_limit}). Баланс возвращён.',
                },
            )

    subscription.device_limit = new_devices
    await finalize_subscription_update(
        db,
        user,
        subscription,
        change_type='devices',
        old_value=old_devices,
        new_value=subscription.device_limit,
        price_paid=max(price_to_charge, 0),
        with_admin_notification_service=with_admin_notification_service,
    )

    return MiniAppSubscriptionUpdateResponse(success=True)


# =============================================================================
# Тарифы для режима продаж "Тарифы"
# =============================================================================


@router.post('/subscription/tariffs', response_model=MiniAppTariffsResponse)
async def get_tariffs_endpoint(
    payload: MiniAppTariffsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppTariffsResponse:
    """Возвращает список доступных тарифов для пользователя."""
    user = await _authorize_miniapp_user(payload.init_data, db)

    ensure_tariffs_mode_enabled(message='Tariffs mode is not enabled')
    tariff_models, current_tariff_model, promo_group_model = await build_tariffs_payload(db, user)

    return MiniAppTariffsResponse(
        success=True,
        sales_mode='tariffs',
        tariffs=tariff_models,
        current_tariff=current_tariff_model,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
        promo_group=promo_group_model,
    )


@router.post('/subscription/tariff/purchase', response_model=MiniAppTariffPurchaseResponse)
async def purchase_tariff_endpoint(
    payload: MiniAppTariffPurchaseRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppTariffPurchaseResponse:
    """Покупка или смена тарифа."""
    user = await _authorize_miniapp_user(payload.init_data, db)
    purchase_context = await build_tariff_purchase_context(
        db,
        user,
        payload.tariff_id,
        payload.period_days,
    )
    tariff = purchase_context.tariff
    price_kopeks = purchase_context.price_kopeks
    period_days = purchase_context.period_days
    is_daily_tariff = purchase_context.is_daily_tariff
    ensure_tariff_purchase_balance(user, price_kopeks)

    subscription = getattr(user, 'subscription', None)

    # Списываем баланс
    description = purchase_context.description
    success = await subtract_user_balance(db, user, price_kopeks, description)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'balance_charge_failed',
                'message': 'Failed to charge balance',
            },
        )

    # Создаём транзакцию
    await create_transaction(
        db=db,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=price_kopeks,
        description=description,
    )

    squads = await resolve_tariff_squads(db, tariff)

    if subscription:
        # Смена/продление тарифа
        subscription = await extend_subscription(
            db=db,
            subscription=subscription,
            days=period_days,
            tariff_id=tariff.id,
            traffic_limit_gb=tariff.traffic_limit_gb,
            device_limit=tariff.device_limit,
            connected_squads=squads,
        )
    else:
        # Создание новой подписки
        from app.database.crud.subscription import create_paid_subscription

        subscription = await create_paid_subscription(
            db=db,
            user_id=user.id,
            duration_days=period_days,
            traffic_limit_gb=tariff.traffic_limit_gb,
            device_limit=tariff.device_limit,
            connected_squads=squads,
            tariff_id=tariff.id,
        )

    # Инициализация daily полей при покупке суточного тарифа
    is_daily_tariff = getattr(tariff, 'is_daily', False)
    if is_daily_tariff:
        subscription.is_daily_paused = False
        subscription.last_daily_charge_at = datetime.now(UTC)
        # Для суточного тарифа end_date = сейчас + 1 день (первый день уже оплачен)
        subscription.end_date = datetime.now(UTC) + timedelta(days=1)
        await db.commit()
        await db.refresh(subscription)

    # Синхронизируем с RemnaWave
    # При покупке тарифа ВСЕГДА сбрасываем трафик в панели
    service = SubscriptionService()
    await service.update_remnawave_user(
        db,
        subscription,
        reset_traffic=True,
        reset_reason='покупка тарифа (miniapp)',
    )

    # Сохраняем корзину для автопродления
    try:
        from app.services.user_cart_service import user_cart_service

        cart_data = {
            'cart_mode': 'extend',
            'subscription_id': subscription.id,
            'period_days': period_days,
            'total_price': price_kopeks,
            'tariff_id': tariff.id,
            'description': f'Продление тарифа {tariff.name} на {period_days} дней',
        }
        await user_cart_service.save_user_cart(user.id, cart_data)
        user_id_display = user.telegram_id or user.email or f'#{user.id}'
        logger.info(
            'Корзина тарифа сохранена для автопродления (miniapp) пользователя', user_id_display=user_id_display
        )
    except Exception as e:
        logger.error('Ошибка сохранения корзины тарифа (miniapp)', error=e)

    await db.refresh(user)

    return MiniAppTariffPurchaseResponse(
        success=True,
        message=f"Тариф '{tariff.name}' успешно активирован",
        subscription_id=subscription.id,
        tariff_id=tariff.id,
        tariff_name=tariff.name,
        new_end_date=subscription.end_date,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )


@router.post('/subscription/tariff/switch/preview')
async def preview_tariff_switch_endpoint(
    payload: MiniAppTariffSwitchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Предпросмотр переключения тарифа - показывает стоимость."""

    user = await _authorize_miniapp_user(payload.init_data, db)

    ensure_tariffs_mode_enabled(message='Tariffs mode is not enabled')

    context = await resolve_tariff_switch_context(
        db,
        user,
        payload.tariff_id,
        unavailable_message='Tariff not available for your promo group',
    )
    current_tariff = context.current_tariff
    new_tariff = context.new_tariff
    promo_group = context.promo_group
    remaining_days = context.remaining_days

    switch_pricing = calculate_switch_pricing(
        current_tariff,
        new_tariff,
        remaining_days,
        promo_group,
        user,
    )
    upgrade_cost = switch_pricing.upgrade_cost
    is_upgrade = switch_pricing.is_upgrade

    balance = user.balance_kopeks or 0
    has_enough = balance >= upgrade_cost
    missing = max(0, upgrade_cost - balance) if not has_enough else 0

    return MiniAppTariffSwitchPreviewResponse(
        can_switch=has_enough,
        current_tariff_id=current_tariff.id if current_tariff else None,
        current_tariff_name=current_tariff.name if current_tariff else None,
        new_tariff_id=new_tariff.id,
        new_tariff_name=new_tariff.name,
        remaining_days=remaining_days,
        upgrade_cost_kopeks=upgrade_cost,
        upgrade_cost_label=settings.format_price(upgrade_cost) if upgrade_cost > 0 else 'Бесплатно',
        balance_kopeks=balance,
        balance_label=settings.format_price(balance),
        has_enough_balance=has_enough,
        missing_amount_kopeks=missing,
        missing_amount_label=settings.format_price(missing) if missing > 0 else '',
        is_upgrade=is_upgrade,
        message=None,
    )


@router.post('/subscription/tariff/switch')
async def switch_tariff_endpoint(
    payload: MiniAppTariffSwitchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Переключение тарифа без изменения даты окончания."""
    user = await _authorize_miniapp_user(payload.init_data, db)

    ensure_tariffs_mode_enabled(message='Tariffs mode is not enabled')

    context = await resolve_tariff_switch_context(
        db,
        user,
        payload.tariff_id,
        unavailable_message='Tariff not available',
    )
    subscription = context.subscription
    current_tariff = context.current_tariff
    new_tariff = context.new_tariff
    promo_group = context.promo_group
    remaining_days = context.remaining_days

    switch_pricing = calculate_switch_pricing(
        current_tariff,
        new_tariff,
        remaining_days,
        promo_group,
        user,
    )
    upgrade_cost = switch_pricing.upgrade_cost
    new_period_days = switch_pricing.new_period_days
    switching_from_daily = switch_pricing.switching_from_daily

    # Списываем доплату если апгрейд
    if upgrade_cost > 0:
        ensure_switch_balance(user, upgrade_cost)
        description = build_switch_charge_description(
            new_tariff_name=new_tariff.name,
            switching_from_daily=switching_from_daily,
            new_period_days=new_period_days,
            remaining_days=remaining_days,
        )
        await execute_switch_charge(
            db=db,
            user=user,
            upgrade_cost=upgrade_cost,
            description=description,
        )
    else:
        # Бесплатный переход (downgrade) — записываем в историю
        description = f"Переход на тариф '{new_tariff.name}'"
        await create_transaction(
            db=db,
            user_id=user.id,
            type=TransactionType.SUBSCRIPTION_PAYMENT,
            amount_kopeks=0,
            description=description,
        )

    await apply_tariff_switch_to_subscription(
        db,
        subscription,
        current_tariff,
        new_tariff,
        new_period_days=new_period_days,
        logger=logger,
    )

    await db.commit()
    await db.refresh(subscription)
    await db.refresh(user)

    # Синхронизируем с RemnaWave (опционально сбрасываем трафик по настройке)
    should_reset_traffic = settings.RESET_TRAFFIC_ON_TARIFF_SWITCH
    try:
        service = SubscriptionService()
        await service.update_remnawave_user(
            db,
            subscription,
            reset_traffic=should_reset_traffic,
            reset_reason='смена тарифа',
        )
    except Exception as e:
        logger.error('Ошибка синхронизации с RemnaWave при смене тарифа', error=e)

    lang = getattr(user, 'language', settings.DEFAULT_LANGUAGE)
    message = build_switch_result_message(lang, new_tariff.name, upgrade_cost)

    return MiniAppTariffSwitchResponse(
        success=True,
        message=message,
        tariff_id=new_tariff.id,
        tariff_name=new_tariff.name,
        charged_kopeks=upgrade_cost,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )


@router.post('/subscription/traffic-topup')
async def purchase_traffic_topup_endpoint(
    payload: MiniAppTrafficTopupRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Докупка трафика для подписки."""
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = _ensure_paid_subscription(user)
    _validate_subscription_id(payload.subscription_id, subscription)

    ensure_tariffs_mode_enabled(message='Traffic top-up is only available in tariffs mode')

    tariff = await get_tariff_for_topup(db, subscription)
    base_price_kopeks = validate_topup_package(subscription, tariff, payload.gb)
    final_price, traffic_discount_percent = calculate_topup_price(
        user,
        subscription,
        base_price_kopeks,
    )

    ensure_topup_balance(user, final_price)
    traffic_description = build_topup_description(payload.gb, traffic_discount_percent)
    await execute_topup_purchase(
        db,
        user,
        subscription,
        package_gb=payload.gb,
        final_price=final_price,
        description=traffic_description,
        logger=logger,
    )

    await db.refresh(user)
    await db.refresh(subscription)

    return MiniAppTrafficTopupResponse(
        success=True,
        message=f'Добавлено {payload.gb} ГБ трафика',
        new_traffic_limit_gb=subscription.traffic_limit_gb,
        new_balance_kopeks=user.balance_kopeks,
        charged_kopeks=final_price,
    )


@router.post('/subscription/daily/toggle-pause')
async def toggle_daily_subscription_pause_endpoint(
    payload: MiniAppDailySubscriptionToggleRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Переключает паузу/активацию суточной подписки."""
    user = await _authorize_miniapp_user(payload.init_data, db)
    subscription = user.subscription

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'no_subscription', 'message': 'No subscription found'},
        )

    tariff = await get_daily_tariff_for_subscription(db, subscription)
    new_paused_state = toggle_pause_state(subscription)

    # Если снимаем с паузы, нужно проверить баланс для активации
    if not new_paused_state:
        was_reactivated = ensure_daily_resume_allowed(user, subscription, tariff)
        if was_reactivated:
            logger.info('✅ Суточная подписка восстановлена из DISABLED в ACTIVE', subscription_id=subscription.id)

    await db.commit()
    await db.refresh(subscription)
    await db.refresh(user)

    await sync_daily_resume_if_needed(user, is_paused=new_paused_state, logger=logger)

    lang = getattr(user, 'language', settings.DEFAULT_LANGUAGE)
    message = build_daily_toggle_message(lang, new_paused_state)

    return MiniAppDailySubscriptionToggleResponse(
        success=True,
        message=message,
        is_paused=new_paused_state,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )
