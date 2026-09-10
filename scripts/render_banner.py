#!/usr/bin/env python3
"""Compose a 1280x640 GitHub social preview banner from the real dial render."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, "/home/rootspectra/creator-dial")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QLinearGradient, QFont, QBrush, QPen, QRadialGradient,
)
from PySide6.QtCore import Qt

RENDERED = "/home/rootspectra/creator-dial/assets/rendered"
OUT = "/home/rootspectra/creator-dial/assets/touchpad-dial-banner.png"

app = QApplication([])
W, H = 1280, 640

pix = QPixmap(W, H)
pix.fill(Qt.black)

p = QPainter(pix)
p.setRenderHint(QPainter.Antialiasing)
p.setRenderHint(QPainter.TextAntialiasing)

# background gradient
grad = QLinearGradient(0, 0, W, H)
grad.setColorAt(0.0, QColor(16, 20, 34))
grad.setColorAt(0.55, QColor(28, 34, 56))
grad.setColorAt(1.0, QColor(10, 12, 22))
p.fillRect(0, 0, W, H, grad)

# subtle radial glow behind the dial
glow = QRadialGradient(W - 430, H - 320, 560)
glow.setColorAt(0.0, QColor(70, 90, 170, 90))
glow.setColorAt(1.0, QColor(0, 0, 0, 0))
p.fillRect(0, 0, W, H, glow)

# decorative ring lines (left)
p.setPen(QPen(QColor(255, 255, 255, 12), 1))
for r in (180, 270, 360, 500):
    p.drawEllipse(int(W*0.06), int(H*0.02), r, r)

# headline
f_title = QFont("DejaVu Sans", 52)
f_title.setBold(True)
p.setPen(QColor(255, 255, 255))
p.setFont(f_title)
p.drawText(70, 250, "Touchpad Dial")

f_tag = QFont("DejaVu Sans", 26)
f_tag.setWeight(QFont.Medium)
p.setPen(QColor(190, 200, 222))
p.setFont(f_tag)
p.drawText(72, 305, "Turn any touchpad into a creative dial.")

f_sub = QFont("DejaVu Sans", 18)
f_sub.setWeight(QFont.Normal)
p.setPen(QColor(140, 150, 175))
p.setFont(f_sub)
p.drawText(72, 358, "Volume · Brightness · Media · Keyboard backlight · Night light · Screenshots · GPU")
p.drawText(72, 398, "Tap, hold, and rotate — no extra hardware. Works on X11 and Wayland.")

# feature chips
chips = ["Gesture-driven", "Open source", "Plugin system", "System tray", "KDE & GNOME"]
chip_x = 72
f_chip = QFont("DejaVu Sans", 14)
f_chip.setBold(False)
for chip in chips:
    tw = p.fontMetrics().horizontalAdvance(chip)
    cw, ch = tw + 40, 34
    p.setBrush(QColor(255, 255, 255, 18))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(chip_x, 430, cw, ch, 17, 17)
    p.setPen(QColor(225, 230, 245))
    p.setFont(f_chip)
    p.drawText(chip_x + 20, 430 + 23, chip)
    chip_x += cw + 16

# the dial UI image (authentic render) on the right
dial = QPixmap(os.path.join(RENDERED, "dial_selection.png"))
dx, dy, dw, dh = W - 620, H - 470, 540, 540
p.setOpacity(0.25)
p.drawPixmap(dx - 30, dy - 30, dw + 60, dh + 60, dial)
p.setOpacity(1.0)
p.drawPixmap(dx, dy, dw, dh, dial)

# small footer
f_foot = QFont("DejaVu Sans", 13)
p.setPen(QColor(110, 118, 140))
p.setFont(f_foot)
p.drawText(72, H - 30, "github.com/AayusX/touchpad-dial  ·  GNU GPL v2  ·  Python  ·  PySide6")

p.end()
pix.save(OUT)
print("wrote", OUT)