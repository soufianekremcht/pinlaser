import math
import time
from collections import deque

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient

FRAME_TIME = 0.016
STEP = 5.0
MAX_SUBDIV = 10


def _clamp01(value):
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def subdivide_segment(p1, p2, now, duration):
    x1, y1, t1 = p1
    x2, y2, t2 = p2
    fade1 = _clamp01(1.0 - (now - t1) / duration)
    fade2 = _clamp01(1.0 - (now - t2) / duration)
    if fade1 <= 0.0 and fade2 <= 0.0:
        return []
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(1, min(int(math.ceil(length / STEP)), MAX_SUBDIV))
    dx, dy = (x2 - x1) / n, (y2 - y1) / n
    dfade = (fade2 - fade1) / n
    return [
        (x1 + dx * i, y1 + dy * i, x1 + dx * (i + 1), y1 + dy * (i + 1),
         fade1 + dfade * (i + 0.5))
        for i in range(n)
    ]


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
        duration = self._trail_duration
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for p1, p2 in zip(pts, pts[1:]):
            for x1, y1, x2, y2, fade in subdivide_segment(p1, p2, now, duration):
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
