import json
from pathlib import Path
from string import Formatter

import pytest


@pytest.mark.parametrize('language', ['ru', 'en'])
@pytest.mark.parametrize(
    ('key', 'placeholders'),
    [
        ('AUTO_PURCHASE_TRAFFIC_SUCCESS', {'traffic_gb', 'new_limit', 'price'}),
        ('AUTO_PURCHASE_DEVICES_SUCCESS', {'devices_to_add', 'new_limit', 'price'}),
    ],
)
def test_auto_purchase_notification_templates_have_expected_placeholders(language, key, placeholders):
    path = Path(__file__).resolve().parents[2] / 'app' / 'localization' / 'locales' / f'{language}.json'
    translations = json.loads(path.read_text(encoding='utf-8'))
    template = translations[key]

    assert {name for _, name, _, _ in Formatter().parse(template) if name is not None} == placeholders
    assert template.format(**dict.fromkeys(placeholders, 10))
