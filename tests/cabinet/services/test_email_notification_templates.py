from app.cabinet.services.email_templates import EmailNotificationTemplates
from app.services.notification_delivery_service import NotificationType


def test_generic_traffic_email_is_localized_and_sanitized():
    templates = EmailNotificationTemplates()

    result = templates.get_generic_notification_template(
        NotificationType.WEBHOOK_SUB_BANDWIDTH_THRESHOLD,
        'ru',
        '<b>Трафик почти закончился</b>\nИспользовано 80%<script>alert(1)</script>',
    )

    assert result is not None
    assert result['subject'] == 'Трафик спецсерверов заканчивается'
    assert 'Трафик почти закончился' in result['body_html']
    assert '<script>' not in result['body_html']
    assert '<b>Трафик почти закончился</b>' not in result['body_html']
    assert result['body_text'] == 'Трафик почти закончился\nИспользовано 80%alert(1)'


def test_device_slots_purchase_email_contains_purchase_details():
    result = EmailNotificationTemplates().get_template(
        NotificationType.DEVICE_SLOTS_PURCHASED,
        'ru',
        {
            'devices_added': 3,
            'new_device_limit': 5,
            'formatted_amount': '300 ₽',
        },
    )

    assert result is not None
    assert result['subject'] == 'Дополнительные устройства подключены'
    assert 'Новый лимит: <strong>5 устройств</strong>' in result['body_html']
    assert '300 ₽' in result['body_html']


def test_traffic_purchase_email_contains_purchase_details():
    result = EmailNotificationTemplates().get_template(
        NotificationType.TRAFFIC_PURCHASED,
        'ru',
        {
            'traffic_gb_added': 100,
            'new_traffic_limit_gb': 135,
            'formatted_amount': '75 ₽',
        },
    )

    assert result is not None
    assert result['subject'] == 'Дополнительный трафик начислен'
    assert 'Добавлено: <strong>100 ГБ</strong>' in result['body_html']
    assert 'Новый лимит: <strong>135 ГБ</strong>' in result['body_html']
