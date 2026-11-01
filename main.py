import logging
import os
import sys

from PySide6.QtCore import QLockFile, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from hotkeys import HotkeyManager
from overlay import OverlayWindow
from settings import AppSettings
from settings_dialog import SettingsDialog

logger = logging.getLogger("pinlaser")


def setup_logging():
    directory = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    os.makedirs(directory, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(
                os.path.join(directory, "pinlaser.log"), encoding="utf-8"
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )


def resource_path(name):
    if getattr(sys, "frozen", False):
        return os.path.join(getattr(sys, "_MEIPASS", "."), name)
    base = os.path.dirname(os.path.abspath(__file__))
    for rel in (os.path.join("assets", name), name):
        candidate = os.path.join(base, rel)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(base, name)


def _draw_fallback_icon():
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QRadialGradient(32, 32, 30, 32, 32)
    grad.setColorAt(0.0, QColor(255, 255, 255))
    grad.setColorAt(0.3, QColor(255, 90, 60))
    grad.setColorAt(1.0, QColor(255, 0, 0, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(grad)
    painter.drawEllipse(6, 6, 52, 52)
    painter.end()
    return pm


def load_icon():
    path = resource_path("app_icon_pin-laser.png")
    if os.path.exists(path):
        pm = QPixmap(path)
        if not pm.isNull():
            pm = pm.scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            return QIcon(pm)
    return QIcon(_draw_fallback_icon())


def acquire_lock():
    directory = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    os.makedirs(directory, exist_ok=True)
    lock = QLockFile(os.path.join(directory, "pinlaser.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, "Pin Laser", "Pin Laser is already running.")
        sys.exit(0)
    return lock


def show_welcome_if_first_run(settings):
    if os.environ.get("PINLASER_SMOKE") or not settings.first_run:
        return
    settings.first_run = False
    settings.save()
    logger.info("showing first-run welcome dialog")
    box = QMessageBox(QMessageBox.Icon.Information, "Pin Laser",
        "Pin Laser is now running.")
    box.setInformativeText(
        "Press Ctrl+Shift+L to show/hide the laser,\n"
        "or left-click the tray icon to toggle it."
    )
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.exec()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pin Laser")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(load_icon())
    setup_logging()

    lock = acquire_lock()
    logger.info("Pin Laser started (pid=%d)", os.getpid())

    settings = AppSettings()
    overlay = OverlayWindow(app, settings)

    tray = QSystemTrayIcon(load_icon(), app)
    tray.setToolTip("Pin Laser - Ctrl+Shift+L toggles the laser pointer")

    menu = QMenu()
    menu.addAction("Show Laser", overlay.show_laser)
    menu.addAction("Hide Laser", overlay.hide_laser)
    menu.addSeparator()
    menu.addAction("Settings...", lambda: SettingsDialog(settings).exec())
    menu.addSeparator()
    menu.addAction("Quit", app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: overlay.toggle_laser()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()

    hotkeys = HotkeyManager(app)
    if hotkeys.register(overlay.toggle_laser):
        logger.info("global hotkey Ctrl+Shift+L registered")
        tray.showMessage(
            "Pin Laser",
            "Press Ctrl+Shift+L to toggle the laser pointer.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )
    else:
        logger.warning("could not register global hotkey Ctrl+Shift+L")
        tray.showMessage(
            "Pin Laser",
            "Could not register hotkey Ctrl+Shift+L (already in use?). Use the tray menu instead.",
            QSystemTrayIcon.MessageIcon.Warning,
            4000,
        )
    app.aboutToQuit.connect(hotkeys.unregister)
    app.aboutToQuit.connect(lambda: logger.info("Pin Laser exiting"))

    if os.environ.get("PINLASER_SMOKE"):
        QTimer.singleShot(2000, app.quit)

    show_welcome_if_first_run(settings)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
