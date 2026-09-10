from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen

CHROME_ALPHA = 90
TEXT_ALPHA = 170


def dashed_frame(widget):
    margin = max(6.0, min(widget.width(), widget.height()) / 24)
    rect = QRectF(widget.rect()).adjusted(margin, margin, -margin, -margin)
    stroke = min(6, max(2.0, margin / 4))
    radius = max(6.0, min(rect.width(), rect.height()) * 0.06)
    return rect, stroke, radius


def chrome_color(widget, alpha=CHROME_ALPHA) -> QColor:
    color = QColor(widget.palette().color(widget.foregroundRole()))
    color.setAlpha(alpha)
    return color


def chrome_color_on_cell(widget) -> QColor:
    """Opaque color matching dashed chrome composited on this cell."""
    fg = widget.palette().color(widget.foregroundRole())
    bg = widget.palette().color(widget.backgroundRole())
    t = CHROME_ALPHA / 255
    return QColor(
        round(fg.red() * t + bg.red() * (1 - t)),
        round(fg.green() * t + bg.green() * (1 - t)),
        round(fg.blue() * t + bg.blue() * (1 - t)),
    )


def paint_outline(
    widget, painter: QPainter | None = None, *, dashed: bool = True
) -> None:
    own_painter = painter is None
    if own_painter:
        painter = QPainter(widget)
    painter.setRenderHint(QPainter.Antialiasing)
    rect, stroke, radius = dashed_frame(widget)
    pen = QPen(chrome_color(widget))
    pen.setWidthF(stroke)
    pen.setStyle(Qt.DashLine if dashed else Qt.SolidLine)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(rect, radius, radius)
    if own_painter:
        painter.end()


def paint_dashed_outline(widget, painter: QPainter | None = None) -> None:
    paint_outline(widget, painter, dashed=True)


def paint_solid_outline(widget, painter: QPainter | None = None) -> None:
    paint_outline(widget, painter, dashed=False)


def idle_disc_rect(widget) -> QRectF:
    side = max(min(widget.width(), widget.height()) * 0.6, 24.0)
    return QRectF(
        (widget.width() - side) / 2,
        (widget.height() - side) / 2,
        side,
        side,
    )


def paint_idle_disc(widget, painter: QPainter | None = None) -> None:
    own_painter = painter is None
    if own_painter:
        painter = QPainter(widget)
    painter.setRenderHint(QPainter.Antialiasing)
    circle = idle_disc_rect(widget)
    painter.setPen(Qt.NoPen)
    painter.setBrush(chrome_color(widget))
    painter.drawEllipse(circle)

    side = circle.width() * 0.36
    square = QRectF(
        circle.center().x() - side / 2,
        circle.center().y() - side / 2,
        side,
        side,
    )
    radius = max(2.0, side * 0.12)
    painter.setBrush(widget.palette().color(widget.backgroundRole()))
    painter.drawRoundedRect(square, radius, radius)
    if own_painter:
        painter.end()
