from __future__ import annotations

from app.services.system_settings_service import BotConfigurationService


def test_ultima_account_linking_mode_is_mapped_to_happ_category() -> None:
    assert BotConfigurationService.CATEGORY_KEY_OVERRIDES['CABINET_ULTIMA_ACCOUNT_LINKING_MODE'] == 'HAPP'


def test_ultima_account_linking_mode_declares_expected_choices() -> None:
    choices = BotConfigurationService.CHOICES['CABINET_ULTIMA_ACCOUNT_LINKING_MODE']

    assert [choice.value for choice in choices] == ['code', 'provider_auth']


def test_ultima_account_linking_mode_has_operator_hint() -> None:
    hint = BotConfigurationService.SETTING_HINTS['CABINET_ULTIMA_ACCOUNT_LINKING_MODE']

    assert 'Сохранение доступа' in hint['description']
    assert 'safe-merge' in hint['warning']


def test_referral_settings_are_grouped_with_russian_hints() -> None:
    referral_keys = [
        'REFERRAL_PROGRAM_ENABLED',
        'SKIP_REFERRAL_CODE',
        'REFERRAL_MINIMUM_TOPUP_KOPEKS',
        'REFERRAL_FIRST_TOPUP_BONUS_KOPEKS',
        'REFERRAL_FIRST_TOPUP_BONUS_DAYS',
        'REFERRAL_INVITER_BONUS_KOPEKS',
        'REFERRAL_INVITER_BONUS_DAYS',
        'REFERRAL_COMMISSION_PERCENT',
        'REFERRAL_NOTIFICATIONS_ENABLED',
        'REFERRAL_NOTIFICATION_RETRY_ATTEMPTS',
        'REFERRAL_PARTNER_SECTION_VISIBLE',
        'REFERRAL_CONTESTS_ENABLED',
        'REFERRAL_WITHDRAWAL_ENABLED',
        'REFERRAL_WITHDRAWAL_MIN_AMOUNT_KOPEKS',
        'REFERRAL_WITHDRAWAL_COOLDOWN_DAYS',
        'REFERRAL_WITHDRAWAL_ONLY_REFERRAL_BALANCE',
        'REFERRAL_WITHDRAWAL_REQUISITES_TEXT',
        'REFERRAL_WITHDRAWAL_NOTIFICATIONS_TOPIC_ID',
        'REFERRAL_WITHDRAWAL_TEST_MODE',
        'REFERRAL_WITHDRAWAL_SUSPICIOUS_MIN_DEPOSIT_KOPEKS',
        'REFERRAL_WITHDRAWAL_SUSPICIOUS_MAX_DEPOSITS_PER_MONTH',
        'REFERRAL_WITHDRAWAL_SUSPICIOUS_NO_PURCHASES_RATIO',
    ]

    BotConfigurationService._definitions = {}
    BotConfigurationService.initialize_definitions()

    for key in referral_keys:
        assert BotConfigurationService.get_definition(key).category_key == 'REFERRAL'
        assert BotConfigurationService.SETTING_HINTS[key]['description']


def test_ultima_traffic_warning_settings_are_grouped_with_webhook_notifications() -> None:
    for key in (
        'ULTIMA_TRAFFIC_WARNING_DEFAULT_PERCENT',
        'ULTIMA_TRAFFIC_WARNING_MESSAGE_RU',
    ):
        assert BotConfigurationService.CATEGORY_KEY_OVERRIDES[key] == 'WEBHOOK_NOTIFICATIONS'
        assert BotConfigurationService.SETTING_HINTS[key]['description']
