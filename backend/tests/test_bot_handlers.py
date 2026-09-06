"""
Tests for the Telegram bot keyboards and help system.
"""
from app.bot.handlers import (
    MESSAGES,
    build_back_keyboard,
    build_help_keyboard,
    build_start_keyboard,
    get_lang,
)


def _buttons(keyboard):
    return [b for row in keyboard.inline_keyboard for b in row]


def test_https_url_gets_a_webapp_button():
    keyboard, notice = build_start_keyboard(
        "https://gremlins.example", "Open", "Help", "Community"
    )
    buttons = _buttons(keyboard)

    webapp = [b for b in buttons if b.web_app]
    assert len(webapp) == 1
    assert webapp[0].web_app.url == "https://gremlins.example"
    assert notice is None


def test_non_https_url_omits_the_webapp_button():
    keyboard, notice = build_start_keyboard(
        "http://localhost:5173", "Open", "Help", "Community"
    )
    buttons = _buttons(keyboard)

    assert not any(b.web_app for b in buttons)
    assert any(b.url for b in buttons)
    assert notice is not None
    assert "localhost:5173" in notice


def test_help_and_community_buttons_always_present():
    for url in ("https://gremlins.example", "http://localhost:5173", "ftp://nope"):
        keyboard, _ = build_start_keyboard(url, "Open", "Help", "Community")
        buttons = _buttons(keyboard)
        assert any(b.callback_data == "help_main" for b in buttons)
        assert any(b.url for b in buttons)


def test_help_keyboard_contains_all_topics():
    for lang in ("uk", "en"):
        kb = build_help_keyboard(lang, "https://gremlins.example")
        buttons = _buttons(kb)
        callbacks = [b.callback_data for b in buttons if b.callback_data]

        assert "help_gremlin" in callbacks
        assert "help_map" in callbacks
        assert "help_camera" in callbacks
        assert "help_raid" in callbacks
        assert "help_security" in callbacks
        assert "help_wallet" in callbacks

        # Webapp button included when https
        webapps = [b for b in buttons if b.web_app]
        assert len(webapps) == 1


def test_back_keyboard():
    kb = build_back_keyboard("uk", "https://gremlins.example")
    buttons = _buttons(kb)
    callbacks = [b.callback_data for b in buttons if b.callback_data]
    assert "help_main" in callbacks


def test_language_resolution():
    assert get_lang("uk") == "uk"
    assert get_lang("uk-UA") == "uk"
    assert get_lang("en") == "en"
    assert get_lang("pl") == "en"
    assert get_lang(None) == "en"


def test_messages_content_parity():
    for lang in ("uk", "en"):
        t = MESSAGES[lang]
        assert "welcome" in t
        assert "help_main" in t
        assert "help_gremlin" in t
        assert "help_map" in t
        assert "help_camera" in t
        assert "help_raid" in t
        assert "help_security" in t
        assert "help_wallet" in t
