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
