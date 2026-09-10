import subprocess
import logging
from typing import Optional
from libevdev import EV_KEY

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.media")


class MediaPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "media"
        self.icon = "multimedia-audio-player"
        self.display_name = "Media"
        self._playing = False

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            self._next_track()
        elif direction == "counterclockwise":
            self._prev_track()
        elif direction == "click":
            self._play_pause()
        elif direction == "long_press":
            self._next_track()

        self._current_value = self._get_media_title()
        return {
            "value": self._current_value,
            "title": self.display_name,
        }

    def _play_pause(self):
        if self._executor:
            self._executor.send_key(EV_KEY.KEY_PLAYPAUSE)
            return
        self._cmd(["playerctl", "play-pause"])

    def _next_track(self):
        if self._executor:
            self._executor.send_key(EV_KEY.KEY_NEXTSONG)
            return
        self._cmd(["playerctl", "next"])

    def _prev_track(self):
        if self._executor:
            self._executor.send_key(EV_KEY.KEY_PREVIOUSSONG)
            return
        self._cmd(["playerctl", "previous"])

    def _cmd(self, args: list):
        try:
            subprocess.run(args, capture_output=True, timeout=2)
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            log.error("Media command failed: %s", e)

    def _get_media_title(self) -> str:
        try:
            result = subprocess.run(
                ["playerctl", "metadata", "--format", "{{playerName}}: {{title}}"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "Media"