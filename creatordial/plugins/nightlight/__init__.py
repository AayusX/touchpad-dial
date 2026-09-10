import subprocess
import logging
import os
from typing import Optional

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.nightlight")

KDE_NIGHT_COLOR_KEY = "Enabled"
KDE_NIGHT_COLOR_GROUP = "NightColor"
KWINRC_PATH = os.path.expanduser("~/.config/kwinrc")
QRUNNER = "qdbus6"


class NightLightPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "nightlight"
        self.icon = "night-light"
        self.display_name = "Night Light"
        self._temperature = 4000
        self._enabled = False

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            self._temperature = min(self._temperature + 500, 6500)
            self._preview(self._temperature)
        elif direction == "counterclockwise":
            self._temperature = max(self._temperature - 500, 1700)
            self._preview(self._temperature)
        elif direction == "click":
            self._toggle()
        elif direction == "long_press":
            pass

        self._refresh_state()
        self._current_value = self._temperature if self._enabled else "Off"
        return {
            "value": self._current_value,
            "unit": "K" if self._enabled else "",
            "title": self.display_name,
        }

    def _refresh_state(self):
        try:
            result = subprocess.run(
                [QRUNNER, "org.kde.KWin", "/org/kde/KWin/NightLight", "org.kde.KWin.NightLight.enabled"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                self._enabled = result.stdout.strip().lower() == "true"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    def _preview(self, temperature: int):
        try:
            subprocess.run(
                [QRUNNER, "org.kde.KWin", "/org/kde/KWin/NightLight", "org.kde.KWin.NightLight.preview",
                 str(temperature)],
                capture_output=True, timeout=3
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    def _toggle(self):
        try:
            result = subprocess.run(
                [QRUNNER, "org.kde.KWin", "/org/kde/KWin/NightLight", "org.kde.KWin.NightLight.enabled"],
                capture_output=True, text=True, timeout=3
            )
            self._enabled = result.returncode == 0 and result.stdout.strip().lower() == "true"
        except (subprocess.SubprocessError, FileNotFoundError):
            self._enabled = False

        new_state = not self._enabled
        self._enabled = new_state

        try:
            # Persist in kwinrc
            subprocess.run(
                ["kwriteconfig6", "--file", "kwinrc", "--group", KDE_NIGHT_COLOR_GROUP,
                 "--key", KDE_NIGHT_COLOR_KEY, "true" if new_state else "false"],
                capture_output=True, timeout=3
            )
            subprocess.run(
                [QRUNNER, "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"],
                capture_output=True, timeout=3
            )

            if new_state:
                self._preview(self._temperature)
            else:
                subprocess.run(
                    [QRUNNER, "org.kde.KWin", "/org/kde/KWin/NightLight", "org.kde.KWin.NightLight.stopPreview"],
                    capture_output=True, timeout=3
                )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            log.error("Failed to toggle night light: %s", e)

    def get_display_info(self) -> dict:
        self._refresh_state()
        return {
            "value": self._temperature if self._enabled else "Off",
            "unit": "K" if self._enabled else "",
            "title": self.display_name,
        }