import json
import socket
import logging
from time import time
from typing import Optional

log = logging.getLogger("creatordial.ui_ipc")

SOCKET_PATH = "/tmp/creatordial.sock"


class UIIPCServer:
    def __init__(self, socket_path: str = SOCKET_PATH):
        self.socket_path = socket_path
        self._sock: Optional[socket.socket] = None

    def start(self):
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self._sock.setblocking(False)
            log.info("UI IPC sender initialized for %s", self.socket_path)
        except Exception as e:
            log.error("Failed to init UI IPC sender: %s", e)
            self._sock = None

    def stop(self):
        if self._sock:
            self._sock.close()
            self._sock = None

    def send(self, data: dict):
        if not self._sock:
            return

        payload = {"ts": time(), **data}
        try:
            self._sock.sendto(
                (json.dumps(payload) + "\n").encode("utf-8"),
                self.socket_path,
            )
        except Exception:
            pass

    def send_enabled(self, enabled: bool):
        self.send({"enabled": enabled})

    def send_value(self, value, unit: Optional[str] = None, title: Optional[str] = None, show_progress: bool = False):
        msg = {"input": "value", "value": value, "title": title}
        if unit:
            msg["unit"] = unit
        if show_progress:
            msg["value_show_only_progress"] = True
        self.send(msg)

    def send_titles(self, titles: list, icons: list, active_title: Optional[str] = None):
        self.send({"titles": titles, "icons": icons, "title": active_title})

    def send_center(self, pressed: bool, title: Optional[str] = None):
        self.send({"input": "center", "value": 1 if pressed else 0, "title": title})

    def send_selection(self, titles: list, icons: list, active_title: Optional[str] = None):
        self.send({"mode": "selection", "titles": titles, "icons": icons, "title": active_title})

    def send_selection_done(self):
        self.send({"mode": "done"})
