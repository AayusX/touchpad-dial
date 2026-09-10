#!/usr/bin/env python3
"""Render real Creator Dial UI screenshots for the GitHub README.

Uses the actual DialWidget (offscreen) so the images are authentic.
The SocketReader is monkeypatched out so we never touch the live socket.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, "/home/rootspectra/creator-dial")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor

# Monkeypatch SocketReader so DialWidget never binds /tmp/creatordial.sock
from creatordial.ui import SocketReader
SocketReader.start = lambda self: None

from creatordial.ui import DialWidget


PLUGINS = [
    {"id": "volume", "title": "Volume", "icon": "audio-volume-high"},
    {"id": "brightness", "title": "Brightness", "icon": "display-brightness-high"},
    {"id": "gpu", "title": "GPU", "icon": "nvidia"},
    {"id": "media", "title": "Media", "icon": "multimedia-audio-player"},
    {"id": "keyboard", "title": "Keyboard", "icon": "input-keyboard"},
    {"id": "screen", "title": "Screen", "icon": "applets-screenshooter"},
    {"id": "nightlight", "title": "Night Light", "icon": "night-light"},
]


def make_widget(size=300):
    app = QApplication.instance() or QApplication([])
    w = DialWidget()
    w.setFixedSize(size, size)
    w._opacity = 1.0
    w._target_opacity = 1.0
    w.show()
    app.processEvents()
    return app, w


def grab(widget):
    pix = QPixmap(widget.size())
    pix.fill(QColor(0, 0, 0, 0))
    widget.render(pix)
    return pix


def save_static(widget, name):
    pix = grab(widget)
    pix.save(f"/home/rootspectra/creator-dial/assets/rendered/{name}")
    print(f"wrote {name}")


def render_static():
    app, w = make_widget()
    w._on_data({"mode": "selection", "titles": [p["title"] for p in PLUGINS],
                "icons": [p["icon"] for p in PLUGINS], "title": "Volume"})
    app.processEvents()
    save_static(w, "dial_selection.png")
    w.deleteLater()


def render_sequence():
    import time
    app, w = make_widget()
    w._on_data({"mode": "selection", "titles": [p["title"] for p in PLUGINS],
                "icons": [p["icon"] for p in PLUGINS], "title": "Volume"})

    frames_dir = "/home/rootspectra/creator-dial/assets/rendered/frames"
    os.makedirs(frames_dir, exist_ok=True)

    names = [p["title"] for p in PLUGINS]
    # highlight cycles through plugins; 7 * 8 frames
    for i in range(56):
        idx = (i // 8) % len(names)
        w._selection_active = names[idx]
        w.update()
        app.processEvents()
        pix = grab(w)
        pix.save(os.path.join(frames_dir, f"frame_{i:03d}.png"))
    w.deleteLater()
    print(f"wrote 56 frames to {frames_dir}")


if __name__ == "__main__":
    os.makedirs("/home/rootspectra/creator-dial/assets/rendered", exist_ok=True)
    render_static()
    render_sequence()