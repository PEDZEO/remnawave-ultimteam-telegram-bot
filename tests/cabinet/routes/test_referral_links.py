from app.cabinet.routes import referral


def test_build_telegram_referral_link_uses_bot_username(monkeypatch) -> None:
    monkeypatch.setattr(type(referral.settings), 'get_bot_username', lambda _self: '@UltimteamBot')

    assert referral._build_telegram_referral_link('ref code/42') == 'https://t.me/UltimteamBot?start=ref%20code%2F42'


def test_build_telegram_referral_link_requires_bot_username(monkeypatch) -> None:
    monkeypatch.setattr(type(referral.settings), 'get_bot_username', lambda _self: '')

    assert referral._build_telegram_referral_link('REF42') == ''
