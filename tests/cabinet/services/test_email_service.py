import smtplib
from unittest.mock import Mock

from app.cabinet.services.email_service import EmailService


def _email_service() -> EmailService:
    service = EmailService()
    service.from_email = 'no-reply@example.com'
    service.from_name = 'Ultimteam'
    service.is_configured = Mock(return_value=True)
    service._send_message = Mock()
    return service


def test_spam_rejection_retries_once_as_plain_text() -> None:
    service = _email_service()
    service._send_message.side_effect = [
        smtplib.SMTPDataError(554, b'5.7.1 Message rejected under suspicion of SPAM'),
        None,
    ]

    sent = service.send_email(
        'user@example.com',
        'Verify email',
        '<p>Open <a href="https://example.com/verify">verification link</a>.</p>',
        'Open https://example.com/verify',
    )

    assert sent is True
    assert service._send_message.call_count == 2
    fallback_message = service._send_message.call_args_list[1].args[1]
    assert fallback_message.get_content_type() == 'text/plain'
    assert fallback_message['Date']
    assert fallback_message['Message-ID']
    assert fallback_message['Auto-Submitted'] == 'auto-generated'


def test_non_spam_smtp_error_is_not_retried() -> None:
    service = _email_service()
    service._send_message.side_effect = smtplib.SMTPDataError(554, b'Mailbox unavailable')

    sent = service.send_email(
        'user@example.com',
        'Verify email',
        '<p>Verification</p>',
        'Verification',
    )

    assert sent is False
    service._send_message.assert_called_once()
