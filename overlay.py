from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from laser import LaserEffect
from win_utils import VK_LBUTTON, VK_RBUTTON, get_cursor_pos, is_button_down


class OverlayWindow(QWidget):
    def __init__(self, app, settings):
        super().__init__()
        self._app = app
        self._settings = settings
        self._laser = LaserEffect(settings)
        self._origin = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._apply_geometry()
        self._app.screenAdded.connect(self._apply_geometry)
        self._app.screenRemoved.connect(self._apply_geometry)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def _apply_geometry(self):
        geo = QRect()
        for screen in self._app.screens():
            geo = geo.united(screen.geometry())
        if geo == self.geometry():
            return
        self._origin = geo.topLeft()
        self.setGeometry(geo)
        if self.isVisible():
            self.show()
            self.raise_()

    def _trail_active(self):
        if not self._settings.trail_on_click:
            return True
        button = self._settings.trail_button
        if button == "right":
            return is_button_down(VK_RBUTTON)
        if button == "either":
            return is_button_down(VK_LBUTTON) or is_button_down(VK_RBUTTON)
        return is_button_down(VK_LBUTTON)

    def _tick(self):
        self._apply_geometry()
        px, py = get_cursor_pos()
        lx, ly = self._to_local(px, py)
        self._laser.update_pos(lx, ly, self._trail_active())
        self.update()

    def _to_local(self, px, py):
        screen = self._app.primaryScreen()
        for s in self._app.screens():
            dpr = s.devicePixelRatio()
            g = s.geometry()
            x0, y0 = g.x() * dpr, g.y() * dpr
            x1, y1 = x0 + g.width() * dpr, y0 + g.height() * dpr
            if x0 <= px < x1 and y0 <= py < y1:
                screen = s
                break
        dpr = screen.devicePixelRatio()
        return px / dpr - self._origin.x(), py / dpr - self._origin.y()

    def show_laser(self):
        self._laser.clear()
        self._apply_geometry()
        self.show()
        self.raise_()
        self._timer.start()

    def hide_laser(self):
        self._timer.stop()
        self.hide()

    def toggle_laser(self):
        if self.isVisible():
            self.hide_laser()
        else:
            self.show_laser()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._laser.paint(painter)
