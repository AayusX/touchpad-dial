import subprocess
import logging
import time
import os
from typing import Optional

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.screen")


class ScreenPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "screen"
        self.icon = "applets-screenshooter"
        self.display_name = "Screenshot"
        self._recording = False
        self._record_pid = None

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            pass
        elif direction == "counterclockwise":
            pass
        elif direction == "click":
            self._take_screenshot()
        elif direction == "long_press":
            self._toggle_recording()

        self._current_value = "Recording" if self._recording else "Ready"
        return {
            "value": self._current_value,
            "title": self.display_name,
        }

    def _take_screenshot(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = f"{self._get_screenshot_dir()}/creator_dial_screenshot_{timestamp}.png"

        for cmd in [
            ["spectacle", "-b", "-n", "-o", filepath],
            ["scrot", filepath],
            ["gnome-screenshot", "-f", filepath],
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and os.path.exists(filepath):
                    log.info("Screenshot saved: %s", filepath)
                    return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        log.warning("No screenshot tool found")

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"{self._get_screenshot_dir()}/creator_dial_recording_{timestamp}.mp4"

            if os.path.exists("/usr/bin/wf-recorder"):
                self._record_pid = subprocess.Popen(
                    ["wf-recorder", "-g", "-f", filepath],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                log.warning("No Wayland screen recorder found (wf-recorder)")
            self._recording = True
            log.info("Screen recording started -> %s", filepath)
        except Exception as e:
            log.error("Failed to start recording: %s", e)

    def _stop_recording(self):
        try:
            if self._record_pid:
                self._record_pid.terminate()
                self._record_pid.wait(timeout=5)
                self._record_pid = None
            self._recording = False
            log.info("Screen recording stopped")
        except Exception as e:
            log.error("Failed to stop recording: %s", e)

    @staticmethod
    def _get_screenshot_dir() -> str:
        pictures_dir = os.path.expanduser("~/Pictures")
        if os.path.exists(pictures_dir) and os.path.isdir(pictures_dir):
            return pictures_dir
        return os.path.expanduser("~")