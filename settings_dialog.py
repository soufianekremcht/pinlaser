from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._original = {
            "trail_on_click": settings.trail_on_click,
            "trail_button": settings.trail_button,
            "color": settings.color,
            "glow_radius": settings.glow_radius,
            "trail_length": settings.trail_length,
        }

        self.setWindowTitle("Pin Laser Settings")
        self.setMinimumWidth(360)

        self._trail_combo = QComboBox()
        self._trail_combo.addItem("Only while clicking", True)
        self._trail_combo.addItem("Always show trail", False)
        self._trail_combo.setCurrentIndex(0 if settings.trail_on_click else 1)

        self._button_combo = QComboBox()
        self._button_combo.addItem("Left button", "left")
        self._button_combo.addItem("Right button", "right")
        self._button_combo.addItem("Either button", "either")
        idx = self._button_combo.findData(settings.trail_button)
        self._button_combo.setCurrentIndex(max(idx, 0))

        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(48, 24)
        self._color_btn.clicked.connect(self._pick_color)

        self._glow_slider = QSlider(Qt.Orientation.Horizontal)
        self._glow_slider.setRange(10, 60)
        self._glow_slider.setValue(int(settings.glow_radius))
        self._glow_value = QLabel()

        self._length_slider = QSlider(Qt.Orientation.Horizontal)
        self._length_slider.setRange(8, 80)
        self._length_slider.setValue(int(settings.trail_length))
        self._length_value = QLabel()

        form = QFormLayout()
        form.addRow("Trail behavior:", self._trail_combo)
        form.addRow("Trail trigger button:", self._button_combo)
        form.addRow("Laser color:", self._color_btn)
        form.addRow("Glow size:", self._slider_row(self._glow_slider, self._glow_value))
        form.addRow("Trail length:", self._slider_row(self._length_slider, self._length_value))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._trail_combo.currentIndexChanged.connect(self._apply_widgets)
        self._button_combo.currentIndexChanged.connect(self._apply_widgets)
        self._glow_slider.valueChanged.connect(self._apply_widgets)
        self._length_slider.valueChanged.connect(self._apply_widgets)

        self._apply_widgets()
        self._refresh_color_button()

    @staticmethod
    def _slider_row(slider, value_label):
        row = QHBoxLayout()
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        return row

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._settings.color), self, "Choose laser color")
        if color.isValid():
            self._settings.color = color.name()
            self._refresh_color_button()

    def _refresh_color_button(self):
        self._color_btn.setStyleSheet(
            f"background-color: {self._settings.color};"
            "border: 1px solid #666; border-radius: 4px;"
        )

    def _apply_widgets(self):
        self._settings.trail_on_click = bool(self._trail_combo.currentData())
        self._settings.trail_button = self._button_combo.currentData()
        self._settings.glow_radius = float(self._glow_slider.value())
        self._settings.trail_length = int(self._length_slider.value())
        self._button_combo.setEnabled(self._settings.trail_on_click)
        self._glow_value.setText(f"{self._glow_slider.value()} px")
        self._length_value.setText(f"{self._length_slider.value()} pts")

    def accept(self):
        self._apply_widgets()
        self._settings.save()
        super().accept()

    def reject(self):
        for key, value in self._original.items():
            setattr(self._settings, key, value)
        super().reject()
