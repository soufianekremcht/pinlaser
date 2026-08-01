from PySide6.QtCore import QSettings

DEFAULTS = {
    "trail_on_click": True,
    "trail_button": "left",
    "color": "#ff2a1a",
    "glow_radius": 28.0,
    "trail_length": 40,
}


class AppSettings:
    def __init__(self, store=None):
        self._store = store if store is not None else QSettings("PinLaser", "PinLaser")
        self.trail_on_click = bool(
            self._store.value("trail_on_click", DEFAULTS["trail_on_click"], type=bool)
        )
        self.trail_button = str(
            self._store.value("trail_button", DEFAULTS["trail_button"], type=str)
        )
        self.color = str(self._store.value("color", DEFAULTS["color"], type=str))
        self.glow_radius = float(
            self._store.value("glow_radius", DEFAULTS["glow_radius"], type=float)
        )
        self.trail_length = int(
            self._store.value("trail_length", DEFAULTS["trail_length"], type=int)
        )

    def save(self):
        self._store.setValue("trail_on_click", self.trail_on_click)
        self._store.setValue("trail_button", self.trail_button)
        self._store.setValue("color", self.color)
        self._store.setValue("glow_radius", self.glow_radius)
        self._store.setValue("trail_length", self.trail_length)
        self._store.sync()
