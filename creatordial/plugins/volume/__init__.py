import subprocess
import logging
from typing import Optional
from libevdev import EV_KEY

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.volume")


class VolumePlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "volume"
        self.icon = "audio-volume-high"
        self.display_name = "Volume"
        self._step = 5

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            self._volume_step("up")
        elif direction == "counterclockwise":
            self._volume_step("down")
        elif direction == "click":
            self._toggle_mute()

        self._current_value = self._get_volume()
        return {
            "value": self._current_value,
            "unit": "%",
            "title": self.display_name,
        }

    def _volume_step(self, direction: str):
        if self._executor:
            key = EV_KEY.KEY_VOLUMEUP if direction == "up" else EV_KEY.KEY_VOLUMEDOWN
            self._executor.send_key(key)
            return

        amount = "+5%" if direction == "up" else "-5%"
        try:
            subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_SINK@", amount],
                capture_output=True, timeout=2
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", amount],
                    capture_output=True, timeout=2
                )
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                log.error("Failed to adjust volume: %s", e)

    def _toggle_mute(self):
        if self._executor:
            self._executor.send_key(EV_KEY.KEY_MUTE)
            return

        try:
            subprocess.run(
                ["wpctl", "set-mute", "@DEFAULT_SINK@", "toggle"],
                capture_output=True, timeout=2
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
                    capture_output=True, timeout=2
                )
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                log.error("Failed to toggle mute: %s", e)

    def _get_volume(self) -> int:
        try:
            result = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    vol = float(parts[1]) * 100
                    return int(vol)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                import re
                m = re.search(r"(\d+)%", result.stdout)
                if m:
                    return int(m.group(1))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return 0