from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.handlers.subscription.purchase import activate_trial
from app.services.trial_activation_service import TrialPaymentInsufficientFunds


@pytest.fixture
def trial_callback_query():
    callback = AsyncMock(spec=CallbackQuery)
    callback.message = AsyncMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def trial_user():
    user = MagicMock(spec=User)
    user.id = 42
    user.telegram_id = 4242
    user.subscription = None
    user.has_had_paid_subscription = False
    user.language = 'ru'
    user.restriction_subscription = False
    user.restriction_reason = None
    return user


@pytest.fixture
def trial_db():
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_activate_trial_uses_trial_price_for_topup_redirect(
    trial_callback_query,
    trial_user,
    trial_db,
):
    error = TrialPaymentInsufficientFunds(required_amount=15900, balance_amount=100)

    mock_keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    with (
        patch('app.services.trial_parameters_service.get_trial_tariff', new=AsyncMock(return_value=None)),
        patch('app.services.trial_parameters_service.get_tariff_by_id', new=AsyncMock(return_value=None)),
        patch(
            'app.handlers.subscription.purchase.charge_trial_activation_if_required',
            side_effect=error,
        ),
        patch(
            'app.handlers.subscription.purchase.create_trial_subscription',
            new=AsyncMock(return_value=MagicMock(id=777)),
        ),
        patch(
            'app.handlers.subscription.purchase.rollback_trial_subscription_activation',
            new=AsyncMock(return_value=True),
        ),
        patch(
            'app.handlers.subscription.purchase.get_texts',
            return_value=MagicMock(
                t=lambda key, default, **kwargs: default,
            ),
        ),
        patch(
            'app.handlers.subscription.purchase.get_insufficient_balance_keyboard',
            return_value=mock_keyboard,
        ) as insufficient_keyboard,
    ):
        await activate_trial(trial_callback_query, trial_user, trial_db)

    insufficient_keyboard.assert_called_once_with(
        trial_user.language,
        amount_kopeks=error.required_amount,
    )
    trial_callback_query.message.edit_text.assert_called_once()
    trial_callback_query.answer.assert_called_once()
