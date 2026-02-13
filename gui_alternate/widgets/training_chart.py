from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetrics


class TrainingChartWidget(QWidget):
    """Custom widget to draw training/validation line charts with Y-axis labels
    and latest-value annotations."""

    def __init__(self, title="Chart", y_label="Value", parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 250)
        self.title = title
        self.y_label = y_label

        # Data storage
        self.training_data = []
        self.validation_data = []

        # Chart appearance
        self.left_margin = 58      # room for Y-axis tick labels
        self.right_margin = 20
        self.top_margin = 30
        self.bottom_margin = 30
        self.training_color = QColor(59, 130, 246)   # Blue
        self.validation_color = QColor(251, 146, 60)  # Orange
        self.bg_color = QColor(30, 30, 50)
        self.grid_color = QColor(64, 64, 96)
        self.axis_color = QColor(100, 100, 140)
        self.text_color = QColor(180, 180, 210)
        self.label_font = QFont("Segoe UI", 8)
        self.value_font = QFont("Segoe UI", 9, QFont.Bold)

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def add_data_point(self, training_value, validation_value):
        """Add a new data point to both series."""
        self.training_data.append(training_value)
        self.validation_data.append(validation_value)
        self.update()

    def clear_data(self):
        """Clear all data points."""
        self.training_data = []
        self.validation_data = []
        self.update()

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _y_range(self):
        """Compute (y_min, y_max) with a small margin."""
        all_vals = self.training_data + self.validation_data
        if not all_vals:
            return 0.0, 1.0
        lo = min(all_vals)
        hi = max(all_vals)
        if hi - lo < 1e-6:
            hi = lo + 1.0
        margin = (hi - lo) * 0.08
        return max(0.0, lo - margin), hi + margin

    def _nice_ticks(self, lo, hi, n_ticks=5):
        """Return n evenly spaced values between lo and hi."""
        step = (hi - lo) / max(n_ticks - 1, 1)
        return [lo + step * i for i in range(n_ticks)]

    def _chart_rect(self):
        x0 = self.left_margin
        y0 = self.top_margin
        w = self.width() - self.left_margin - self.right_margin
        h = self.height() - self.top_margin - self.bottom_margin
        return x0, y0, max(w, 1), max(h, 1)

    def _val_to_y(self, value, y_min, y_max, cy, ch):
        frac = (value - y_min) / max(y_max - y_min, 1e-9)
        return cy + ch * (1.0 - frac)

    @staticmethod
    def _fmt(v):
        """Format a value for display."""
        if abs(v) < 0.01:
            return f"{v:.5f}"
        if abs(v) < 1:
            return f"{v:.4f}"
        return f"{v:.2f}"

    # -----------------------------------------------------------------
    # Painting
    # -----------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)

        cx, cy, cw, ch = self._chart_rect()
        y_min, y_max = self._y_range()
        ticks = self._nice_ticks(y_min, y_max, 5)

        self._draw_grid(painter, cx, cy, cw, ch, ticks, y_min, y_max)
        self._draw_axes(painter, cx, cy, cw, ch)
        self._draw_y_labels(painter, cx, cy, ch, ticks, y_min, y_max)
        self._draw_x_labels(painter, cx, cy, cw, ch)

        if len(self.training_data) > 1:
            self._draw_line(painter, self.training_data, cx, cy, cw, ch,
                            y_min, y_max, self.training_color)
        if len(self.validation_data) > 1:
            self._draw_line(painter, self.validation_data, cx, cy, cw, ch,
                            y_min, y_max, self.validation_color)

        # Latest-value annotations (drawn last so they sit on top)
        if self.training_data:
            self._draw_value_label(painter, self.training_data, cx, cy, cw, ch,
                                   y_min, y_max, self.training_color, align_above=True)
        if self.validation_data:
            self._draw_value_label(painter, self.validation_data, cx, cy, cw, ch,
                                   y_min, y_max, self.validation_color, align_above=False)

        painter.end()

    # -- sub-drawing routines --

    def _draw_axes(self, painter, cx, cy, cw, ch):
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawLine(cx, cy, cx, cy + ch)
        painter.drawLine(cx, cy + ch, cx + cw, cy + ch)

    def _draw_grid(self, painter, cx, cy, cw, ch, ticks, y_min, y_max):
        pen = QPen(self.grid_color, 1, Qt.DotLine)
        painter.setPen(pen)
        for t in ticks:
            py = int(self._val_to_y(t, y_min, y_max, cy, ch))
            painter.drawLine(cx, py, cx + cw, py)

    def _draw_y_labels(self, painter, cx, cy, ch, ticks, y_min, y_max):
        painter.setFont(self.label_font)
        painter.setPen(self.text_color)
        fm = QFontMetrics(self.label_font)
        for t in ticks:
            py = self._val_to_y(t, y_min, y_max, cy, ch)
            label = self._fmt(t)
            tw = fm.horizontalAdvance(label)
            painter.drawText(int(cx - tw - 6), int(py + fm.ascent() / 2 - 1), label)

    def _draw_x_labels(self, painter, cx, cy, cw, ch):
        n = max(len(self.training_data), len(self.validation_data))
        if n < 2:
            return
        painter.setFont(self.label_font)
        painter.setPen(self.text_color)
        fm = QFontMetrics(self.label_font)

        max_labels = max(1, cw // 50)
        step = max(1, (n - 1) // max_labels)
        for i in range(0, n, step):
            px = cx + cw * i / (n - 1)
            label = str(i + 1)
            tw = fm.horizontalAdvance(label)
            painter.drawText(int(px - tw / 2), int(cy + ch + fm.ascent() + 4), label)

        # Always show last epoch
        if (n - 1) % step != 0:
            px = cx + cw
            label = str(n)
            tw = fm.horizontalAdvance(label)
            painter.drawText(int(px - tw / 2), int(cy + ch + fm.ascent() + 4), label)

    def _draw_line(self, painter, data, cx, cy, cw, ch, y_min, y_max, color):
        painter.setPen(QPen(color, 2))
        path = QPainterPath()
        n = len(data)
        for i, v in enumerate(data):
            px = cx + cw * i / max(n - 1, 1)
            py = self._val_to_y(v, y_min, y_max, cy, ch)
            if i == 0:
                path.moveTo(QPointF(px, py))
            else:
                path.lineTo(QPointF(px, py))
        painter.drawPath(path)

    def _draw_value_label(self, painter, data, cx, cy, cw, ch,
                          y_min, y_max, color, align_above=True):
        """Draw a rounded pill with the latest value next to the last point."""
        if not data:
            return
        n = len(data)
        v = data[-1]
        px = cx + cw * (n - 1) / max(n - 1, 1)
        py = self._val_to_y(v, y_min, y_max, cy, ch)

        # Dot
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(px, py), 4, 4)

        # Label
        label = self._fmt(v)
        painter.setFont(self.value_font)
        fm = QFontMetrics(self.value_font)
        tw = fm.horizontalAdvance(label)
        th = fm.height()

        pad = 4
        box_w = tw + pad * 2
        box_h = th + pad
        offset_y = -(box_h + 6) if align_above else 8

        bx = min(px - box_w / 2, cx + cw - box_w)
        bx = max(bx, cx)
        by = py + offset_y
        by = max(by, cy)
        by = min(by, cy + ch - box_h)

        # Pill background
        painter.setPen(Qt.NoPen)
        bg = QColor(color)
        bg.setAlpha(180)
        painter.setBrush(bg)
        painter.drawRoundedRect(QRectF(bx, by, box_w, box_h), 4, 4)

        # Text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(int(bx + pad), int(by + fm.ascent() + pad / 2), label)
