import math
import time
from collections import deque

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient

FRAME_TIME = 0.016


class LaserEffect:
    def __init__(self, settings):
        self._settings = settings
        self._trail = deque()
        self._pos = (0.0, 0.0)
        self._clock = time.monotonic

    @property
    def _max_trail(self):
        return max(1, int(self._settings.trail_length))

    @property
    def _trail_duration(self):
        return self._max_trail * FRAME_TIME

    @property
    def _glow_radius(self):
        return max(1.0, float(self._settings.glow_radius))

    @property
    def _trail_width(self):
        return max(4.0, self._glow_radius * 0.55)

    @property
    def _color(self):
        return QColor(self._settings.color)

    def clear(self):
        self._trail.clear()

    def update_pos(self, x, y, trail_active):
        now = self._clock()
        self._pos = (float(x), float(y))
        if trail_active:
            self._trail.append((self._pos[0], self._pos[1], now))
        while self._trail and now - self._trail[0][2] > self._trail_duration:
            self._trail.popleft()
        while len(self._trail) > self._max_trail:
            self._trail.popleft()

    def paint(self, painter):
        now = self._clock()
        self._draw_trail(painter, now)
        self._draw_dot(painter, now)

    def _draw_trail(self, painter, now):
        pts = list(self._trail)
        if len(pts) < 2:
            return
        base = self._color
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for (x1, y1, _), (x2, y2, t2) in zip(pts, pts[1:]):
            age = (now - t2) / self._trail_duration
            if age >= 1.0:
                continue
            fade = 1.0 - age
            alpha = int(220 * fade)
            width = 1.0 + self._trail_width * fade
            painter.setPen(
                QPen(
                    QColor(base.red(), base.green(), base.blue(), alpha),
                    width,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_dot(self, painter, now):
        x, y = self._pos
        base = self._color
        pulse = 1.0 + 0.05 * math.sin(now * 7.0)
        radius = self._glow_radius * pulse
        grad = QRadialGradient(QPointF(x, y), radius)
        grad.setColorAt(0.00, QColor(255, 255, 255, 255))
        grad.setColorAt(0.12, base.lighter(150))
        mid = QColor(base)
        mid.setAlpha(190)
        grad.setColorAt(0.40, mid)
        end = QColor(base)
        end.setAlpha(0)
        grad.setColorAt(1.00, end)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawEllipse(QPointF(x, y), radius, radius)
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.drawEllipse(QPointF(x, y), 2.6, 2.6)
