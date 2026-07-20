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


def test_generated_plain_text_removes_styles_and_keeps_content() -> None:
    service = _email_service()

    sent = service.send_email(
        'user@example.com',
        'Подписка активирована',
        """
        <!doctype html>
        <html>
          <head>
            <style>body { color: #fff; } .container { padding: 20px; }</style>
          </head>
          <body>
            <div class="container">
              <h2>Подписка активирована</h2>
              <p>Действует до: <strong>21.07.2026</strong></p>
              <a href="https://cabinet.example.com">Открыть кабинет</a>
            </div>
          </body>
        </html>
        """,
    )

    assert sent is True
    message = service._send_message.call_args.args[1]
    plain_part = message.get_payload()[0]
    plain_text = plain_part.get_payload(decode=True).decode(plain_part.get_content_charset())
    assert 'body {' not in plain_text
    assert '.container' not in plain_text
    assert 'Подписка активирована' in plain_text
    assert 'Действует до: 21.07.2026' in plain_text
    assert 'Открыть кабинет (https://cabinet.example.com)' in plain_text


def test_spam_fallback_does_not_send_css_as_message_body() -> None:
    service = _email_service()
    service._send_message.side_effect = [
        smtplib.SMTPDataError(554, b'5.7.1 Message rejected under suspicion of SPAM'),
        None,
    ]

    sent = service.send_email(
        'user@example.com',
        'Traffic warning',
        '<style>body { background: red; }</style><h2>Traffic is running low</h2><p>2 GB left</p>',
    )

    assert sent is True
    fallback_message = service._send_message.call_args_list[1].args[1]
    fallback_text = fallback_message.get_payload(decode=True).decode(fallback_message.get_content_charset())
    assert 'body {' not in fallback_text
    assert fallback_text == 'Traffic is running low\n2 GB left'


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


def test_verification_code_email_contains_no_link() -> None:
    service = _email_service()
    service.send_email = Mock(return_value=True)

    sent = service.send_verification_email(
        'user@example.com',
        '123456',
        'https://example.com/verify',
        language='ru',
    )

    assert sent is True
    _, _, body_html, body_text = service.send_email.call_args.args
    assert '123456' in body_html
    assert '123456' in body_text
    assert 'https://' not in body_html
    assert 'https://' not in body_text
