import sys
import os
import json
import socket
import logging
import math
import signal
from time import time

from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QPropertyAnimation,
    QEasingCurve, Signal, QObject, QThread, QSize
)
from PySide6.QtGui import (
    QPainter, QPen, QColor, QPainterPath, QIcon,
    QRadialGradient, QConicalGradient, QLinearGradient,
    QFont, QFontDatabase
)

log = logging.getLogger("creatordial.ui")

SOCKET_PATH = "/tmp/creatordial.sock"


class SocketReader(QObject):
    data_received = Signal(dict)

    def __init__(self):
        super().__init__()
        self._sock = None
        self._buffer = ""

    def start(self):
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except Exception:
                pass

        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self._sock.bind(SOCKET_PATH)
        self._sock.setblocking(False)

        self._timer = QTimer()
        self._timer.timeout.connect(self._read)
        self._timer.start(30)
        log.info("Socket reader started on %s", SOCKET_PATH)

    def stop(self):
        if self._timer:
            self._timer.stop()
        if self._sock:
            self._sock.close()

    def _read(self):
        if not self._sock:
            return
        try:
            data, _ = self._sock.recvfrom(4096)
            self._buffer += data.decode()
        except BlockingIOError:
            return
        except Exception:
            return

        while "}" in self._buffer:
            idx = self._buffer.find("}") + 1
            chunk = self._buffer[:idx]
            self._buffer = self._buffer[idx:]
            try:
                obj = json.loads(chunk)
                self.data_received.emit(obj)
            except json.JSONDecodeError:
                pass


class DialWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 300)

        self._selection_mode = False
        self._selection_titles = []
        self._selection_icons = []
        self._selection_active = ""
        self._last_input_time = 0.0

        self._opacity = 0.0
        self._target_opacity = 0.0

        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._animate_fade)
        self._fade_timer.start(16)

        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_hide)

        self._socket_reader = SocketReader()
        self._socket_reader.data_received.connect(self._on_data)
        self._socket_reader.start()

    def _on_data(self, obj: dict):
        mode = obj.get("mode")
        if mode == "selection":
            self._selection_mode = True
            self._selection_titles = obj.get("titles", [])
            self._selection_icons = obj.get("icons", [])
            self._selection_active = obj.get("title", "")
            self._target_opacity = 1.0
            self.show()
            self.raise_()
            self.activateWindow()
            self._last_input_time = time()
            self._hide_timer.start(2000)
            self.update()

        elif mode == "done":
            self._selection_mode = False
            self._selection_titles = []
            self._selection_icons = []
            self._selection_active = ""
            self._target_opacity = 0.0
            self.update()
            return

        title = obj.get("title")
        if title is not None and self._selection_mode:
            self._selection_active = title
            self._last_input_time = time()
            self._hide_timer.start(2000)
            self.update()

    def _start_hide(self):
        self._target_opacity = 0.0
        self.update()

    def _animate_fade(self):
        if abs(self._opacity - self._target_opacity) > 0.02:
            diff = self._target_opacity - self._opacity
            self._opacity += diff * 0.15
            self.update()
        else:
            self._opacity = self._target_opacity
            if self._target_opacity == 0.0:
                self._selection_mode = False
                self.hide()

    def paintEvent(self, event):
        if self._opacity < 0.01 or not self._selection_mode:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setOpacity(self._opacity)

        w, h = self.width(), self.height()
        margin = 30
        max_d = min(w - 2 * margin, h - 2 * margin)
        outer_d = max_d
        center_d = max_d * 0.35

        cx, cy = w / 2, h / 2 + 10

        outer_rect = QRectF(cx - outer_d / 2, cy - outer_d / 2, outer_d, outer_d)
        center_rect = QRectF(cx - center_d / 2, cy - center_d / 2, center_d, center_d)

        self._draw_background(painter, outer_rect, center_rect)
        self._draw_ring(painter, outer_rect, center_rect)

        if self._selection_titles:
            self._draw_segments(painter, outer_rect, center_rect)

        self._draw_center(painter, center_rect)

    def _draw_background(self, painter, outer_rect, center_rect):
        painter.setPen(Qt.NoPen)

        gradient = QRadialGradient(outer_rect.center(), outer_rect.width() / 2)
        gradient.setColorAt(0.0, QColor(30, 35, 50, 200))
        gradient.setColorAt(0.7, QColor(20, 25, 40, 220))
        gradient.setColorAt(1.0, QColor(15, 18, 28, 240))
        painter.setBrush(gradient)
        painter.drawEllipse(outer_rect)

    def _draw_ring(self, painter, outer_rect, center_rect):
        pen = QPen(QColor(165, 152, 138, 60), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        num_ticks = 100
        for i in range(num_ticks):
            angle = i * 360.0 / num_ticks
            rad = math.radians(angle - 90)
            inner_r = outer_rect.width() / 2 - 8
            outer_r = outer_rect.width() / 2

            x1 = outer_rect.center().x() + inner_r * math.cos(rad)
            y1 = outer_rect.center().y() + inner_r * math.sin(rad)
            x2 = outer_rect.center().x() + outer_r * math.cos(rad)
            y2 = outer_rect.center().y() + outer_r * math.sin(rad)

            tick_pen = QPen(QColor(165, 152, 138, 40), 1)
            painter.setPen(tick_pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_segments(self, painter, outer_rect, center_rect):
        n = len(self._selection_titles)
        if n == 0:
            return

        slice_angle = 360.0 / n

        font = QFont()
        font.setPixelSize(int(center_rect.width() * 0.08))
        painter.setFont(font)

        for idx in range(n):
            start = idx * slice_angle

            path = QPainterPath()
            path.moveTo(outer_rect.center())
            path.arcTo(outer_rect, -start, slice_angle)
            path.closeSubpath()

            hole = QPainterPath()
            hole.addEllipse(center_rect)
            segment = path.subtracted(hole)

            is_active = (self._selection_titles[idx] == self._selection_active)

            if is_active:
                painter.setPen(Qt.NoPen)
                active_grad = QConicalGradient(
                    outer_rect.center(), -start - slice_angle / 2
                )
                active_grad.setColorAt(0, QColor(165, 152, 138, 180))
                active_grad.setColorAt(0.5, QColor(165, 152, 138, 100))
                active_grad.setColorAt(1, QColor(165, 152, 138, 180))
                painter.setBrush(active_grad)
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(Qt.NoBrush)

            painter.drawPath(segment)

            seg_pen = QPen(QColor(40, 45, 60, 150), 1)
            painter.setPen(seg_pen)
            painter.drawPath(segment)

            title_text = self._selection_titles[idx]
            has_icon = idx < len(self._selection_icons) and self._selection_icons[idx]

            if title_text and not has_icon:
                angle_deg = start + slice_angle / 2
                angle_rad = math.radians(angle_deg - 90)
                r = outer_rect.width() / 2 * 0.78

                x = outer_rect.center().x() + r * math.cos(angle_rad)
                y = outer_rect.center().y() + r * math.sin(angle_rad)

                text_rect = QRectF(
                    x - center_rect.width() * 0.2,
                    y - center_rect.height() * 0.08,
                    center_rect.width() * 0.4,
                    center_rect.height() * 0.16,
                )

                text_color = QColor(185, 186, 185) if is_active else QColor(120, 125, 130)
                painter.setPen(text_color)
                painter.drawText(text_rect, Qt.AlignCenter, title_text)

    def _draw_center(self, painter, center_rect):
        painter.setPen(Qt.NoPen)

        grad = QRadialGradient(center_rect.center(), center_rect.width() / 2)
        grad.setColorAt(0, QColor(38, 42, 58))
        grad.setColorAt(1, QColor(28, 32, 48))
        painter.setBrush(grad)

        painter.drawEllipse(center_rect)

        border_pen = QPen(QColor(80, 85, 100, 100), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_rect)

        font = QFont()
        font.setPixelSize(int(center_rect.width() * 0.12))
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)

        painter.setPen(QColor(185, 186, 185))

        title_text = self._selection_active or "Select"
        text_rect = QRectF(
            center_rect.x(),
            center_rect.y() + center_rect.height() * 0.2,
            center_rect.width(),
            center_rect.height() * 0.3,
        )
        painter.drawText(text_rect, Qt.AlignCenter, title_text)

    def closeEvent(self, event):
        self._hide_timer.stop()
        self._socket_reader.stop()
        super().closeEvent(event)


class CreatorDialApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("Creator Dial")
        self.app.setApplicationDisplayName("Creator Dial")

        self._dial_widget = DialWidget()
        self._tray = self._create_tray()

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon()
        tray.setIcon(QIcon.fromTheme("input-gaming"))
        tray.setToolTip("Creator Dial")

        menu = QMenu()

        show_action = menu.addAction("Show Dial")
        show_action.triggered.connect(self._show_dial)

        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()

        return tray

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_dial()

    def _show_dial(self):
        if self._dial_widget._selection_mode:
            self._dial_widget.hide()
        else:
            self._dial_widget.show()

    def _open_settings(self):
        log.info("Settings dialog not yet implemented")

    def _quit(self):
        self._dial_widget.close()
        self.app.quit()

    def run(self):
        signal.signal(signal.SIGINT, lambda sig, frame: self.app.quit())
        return self.app.exec()
