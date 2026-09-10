import subprocess
import logging
from typing import Optional
from libevdev import EV_KEY

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.brightness")

BACKLIGHT_DIR = "/sys/class/backlight/intel_backlight"
DBUS_SERVICE = "org.kde.ScreenBrightness"
DBUS_PATH = "/org/kde/ScreenBrightness/display0"


class BrightnessPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "brightness"
        self.icon = "display-brightness-high"
        self.display_name = "Brightness"
        self._step = 5

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            self._brightness_step("up")
        elif direction == "counterclockwise":
            self._brightness_step("down")
        elif direction == "click":
            pass
        elif direction == "long_press":
            pass

        self._current_value = self._get_brightness()
        return {
            "value": self._current_value,
            "unit": "%",
            "title": self.display_name,
        }

    def _brightness_step(self, direction: str):
        current = self._get_brightness()
        target = min(current + self._step, 100) if direction == "up" else max(current - self._step, 0)

        # KDE PowerDevil D-Bus interface (0-10000 scale)
        try:
            subprocess.run(
                ["busctl", "--user", "call", DBUS_SERVICE, DBUS_PATH,
                 "org.kde.ScreenBrightness.Display", "SetBrightness",
                 "iu", str(int(target * 100)), "0"],
                capture_output=True, timeout=3
            )
            return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fallback: virtual keys
        if self._executor:
            key = EV_KEY.KEY_BRIGHTNESSUP if direction == "up" else EV_KEY.KEY_BRIGHTNESSDOWN
            self._executor.send_key(key)
            return

        try:
            amount = "+10%" if direction == "up" else "-10%"
            subprocess.run(
                ["brightnessctl", "set", amount],
                capture_output=True, timeout=2
            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            log.error("Failed to adjust brightness: %s", e)

    def _get_brightness(self) -> int:
        # Try KDE D-Bus current brightness
        try:
            result = subprocess.run(
                ["busctl", "--user", "get-property", DBUS_SERVICE, DBUS_PATH,
                 "org.kde.ScreenBrightness.Display", "Brightness"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                import re
                m = re.search(r"i (\d+)", result.stdout)
                max_m = None
                res_max = subprocess.run(
                    ["busctl", "--user", "get-property", DBUS_SERVICE, DBUS_PATH,
                     "org.kde.ScreenBrightness.Display", "MaxBrightness"],
                    capture_output=True, text=True, timeout=3
                )
                if res_max.returncode == 0:
                    mm = re.search(r"i (\d+)", res_max.stdout)
                    if mm:
                        max_m = int(mm.group(1))
                if m and max_m and max_m > 0:
                    return int(int(m.group(1)) / max_m * 100)
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            pass

        try:
            with open(f"{BACKLIGHT_DIR}/brightness") as f:
                current = int(f.read().strip())
            with open(f"{BACKLIGHT_DIR}/max_brightness") as f:
                maximum = int(f.read().strip())
            if maximum > 0:
                return int(current / maximum * 100)
        except (FileNotFoundError, PermissionError, ValueError):
            pass

        try:
            result = subprocess.run(
                ["brightnessctl", "-m"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                for part in parts:
                    if part.endswith("%"):
                        return int(part.rstrip("%"))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return 0