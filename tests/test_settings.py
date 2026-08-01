import os
import tempfile

from PySide6.QtCore import QSettings

from settings import AppSettings, DEFAULTS


def make_store(path):
    return QSettings(path, QSettings.Format.IniFormat)


def test_defaults():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "settings.ini")
        store = make_store(path)
        store.clear()
        settings = AppSettings(store)
        assert settings.trail_on_click == DEFAULTS["trail_on_click"]
        assert settings.trail_button == DEFAULTS["trail_button"]
        assert settings.color == DEFAULTS["color"]
        assert settings.glow_radius == DEFAULTS["glow_radius"]
        assert settings.trail_length == DEFAULTS["trail_length"]


def test_save_load_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "settings.ini")
        store = make_store(path)
        settings = AppSettings(store)
        settings.trail_on_click = False
        settings.trail_button = "right"
        settings.color = "#00ff00"
        settings.glow_radius = 50.0
        settings.trail_length = 12
        settings.save()

        store = make_store(path)
        loaded = AppSettings(store)
        assert loaded.trail_on_click is False
        assert loaded.trail_button == "right"
        assert loaded.color == "#00ff00"
        assert loaded.glow_radius == 50.0
        assert loaded.trail_length == 12
