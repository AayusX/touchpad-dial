import subprocess
import logging
from typing import Optional
from libevdev import EV_KEY

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.keyboard")

BRIGHTNESS_FILE = "/sys/class/leds/asus::kbd_backlight/brightness"
MAX_BRIGHTNESS_FILE = "/sys/class/leds/asus::kbd_backlight/max_brightness"


class KeyboardPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "keyboard"
        self.icon = "input-keyboard"
        self.display_name = "Keyboard Backlight"
        self._brightness = 0
        self._levels = [0, 1, 2, 3]
        self._level_index = 1

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            self._step("up")
        elif direction == "counterclockwise":
            self._step("down")
        elif direction == "click":
            self._toggle_backlight()
        elif direction == "long_press":
            pass

        self._brightness = self._get_backlight()
        self._level_index = self._brightness_to_index(self._brightness)
        self._current_value = self._brightness
        return {
            "value": self._current_value,
            "unit": "/3",
            "title": self.display_name,
        }

    def _step(self, direction: str):
        if self._executor:
            key = EV_KEY.KEY_KBDILLUMUP if direction == "up" else EV_KEY.KEY_KBDILLUMDOWN
            self._executor.send_key(key)
            return

        self._brightness = self._get_backlight()
        if direction == "up":
            self._level_index = min(self._level_index + 1, len(self._levels) - 1)
        else:
            self._level_index = max(self._level_index - 1, 0)
        self._set_backlight(self._levels[self._level_index])

    def _set_backlight(self, level: int):
        try:
            with open(BRIGHTNESS_FILE, "w") as f:
                f.write(str(level))
            self._brightness = level
        except (FileNotFoundError, PermissionError) as e:
            log.error("Failed to set keyboard backlight: %s", e)

    def _get_backlight(self) -> int:
        try:
            with open(BRIGHTNESS_FILE) as f:
                return int(f.read().strip())
        except (FileNotFoundError, PermissionError):
            pass
        return 0

    def _brightness_to_index(self, value: int) -> int:
        max_val = 3
        try:
            with open(MAX_BRIGHTNESS_FILE) as f:
                max_val = int(f.read().strip())
        except (FileNotFoundError, PermissionError, ValueError):
            pass
        if max_val <= 0:
            max_val = 3
        return int(round(value / max_val * (len(self._levels) - 1)))

    def _toggle_backlight(self):
        if self._executor:
            self._executor.send_key(EV_KEY.KEY_KBDILLUMTOGGLE)
            return

        if self._get_backlight() > 0:
            self._set_backlight(0)
            self._level_index = 0
        else:
            self._set_backlight(2)
            self._level_index = 2

    def get_display_info(self) -> dict:
        self._brightness = self._get_backlight()
        self._current_value = self._brightness
        return {
            "value": self._current_value,
            "unit": "/3",
            "title": self.display_name,
        }