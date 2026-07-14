import pytest
from fastapi import HTTPException

from app.cabinet.routes.admin_settings import _coerce_value


def test_traffic_warning_percent_accepts_remnawave_range() -> None:
    assert _coerce_value('ULTIMA_TRAFFIC_WARNING_DEFAULT_PERCENT', 25) == 25
    assert _coerce_value('ULTIMA_TRAFFIC_WARNING_DEFAULT_PERCENT', 95) == 95


@pytest.mark.parametrize('value', [24, 96])
def test_traffic_warning_percent_rejects_values_outside_remnawave_range(value: int) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _coerce_value('ULTIMA_TRAFFIC_WARNING_DEFAULT_PERCENT', value)

    assert exc_info.value.status_code == 400


def test_traffic_warning_message_accepts_supported_variables() -> None:
    message = 'Использовано {percent}%, осталось {remaining_gb} ГБ'
    assert _coerce_value('ULTIMA_TRAFFIC_WARNING_MESSAGE_RU', message) == message


@pytest.mark.parametrize(
    'message',
    [
        'Неизвестная переменная {days}',
        'Некорректная скобка {percent',
        'Модификатор {percent:.2f}',
    ],
)
def test_traffic_warning_message_rejects_unsafe_templates(message: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _coerce_value('ULTIMA_TRAFFIC_WARNING_MESSAGE_RU', message)

    assert exc_info.value.status_code == 400
