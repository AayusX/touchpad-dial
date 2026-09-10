import json
import logging
import threading
from typing import Optional, Callable

log = logging.getLogger("creatordial.dbus")


class DBusServer:
    def __init__(self):
        self._bus_name = "org.creatordial.Dial"
        self._object_path = "/org/creatordial/Dial"
        self._interface = "org.creatordial.Dial"
        self._callbacks: dict[str, list[Callable]] = {}
        self._properties: dict = {
            "active": False,
            "current_plugin": "volume",
            "current_value": 0,
            "current_profile": "default",
        }

    def start(self):
        log.info("D-Bus server started (bus=%s)", self._bus_name)

    def stop(self):
        log.info("D-Bus server stopped")

    def emit_signal(self, signal_name: str, **kwargs):
        for cb in self._callbacks.get(signal_name, []):
            try:
                cb(**kwargs)
            except Exception as e:
                log.error("D-Bus signal callback error: %s", e)

    def connect_signal(self, signal_name: str, callback: Callable):
        if signal_name not in self._callbacks:
            self._callbacks[signal_name] = []
        self._callbacks[signal_name].append(callback)

    def update_property(self, name: str, value):
        self._properties[name] = value
        self.emit_signal("PropertiesChanged", name=name, value=value)

    def get_property(self, name: str):
        return self._properties.get(name)
