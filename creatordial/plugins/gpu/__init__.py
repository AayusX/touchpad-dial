import subprocess
import logging
from typing import Optional

from .. import BasePlugin

log = logging.getLogger("creatordial.plugin.gpu")


class GPUPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "gpu"
        self.icon = "nvidia"
        self.display_name = "GPU"
        self._mode = "balanced"
        self._modes = ["silent", "balanced", "performance"]
        self._mode_index = 1

    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        if direction == "clockwise":
            self._mode_index = min(self._mode_index + 1, len(self._modes) - 1)
            self._mode = self._modes[self._mode_index]
            self._set_power_mode(self._mode)
        elif direction == "counterclockwise":
            self._mode_index = max(self._mode_index - 1, 0)
            self._mode = self._modes[self._mode_index]
            self._set_power_mode(self._mode)
        elif direction == "click":
            pass
        elif direction == "long_press":
            pass

        info = self._get_gpu_info()
        self._current_value = info.get("usage", 0)

        return {
            "value": self._current_value,
            "unit": "%",
            "title": f"GPU · {self._mode}",
        }

    def _get_gpu_info(self) -> dict:
        info = {"usage": 0, "temp": 0, "vram": 0, "power": 0}
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                if len(parts) >= 5:
                    info = {
                        "usage": int(parts[0]),
                        "temp": int(parts[1]),
                        "vram_used": int(parts[2]),
                        "vram_total": int(parts[3]),
                        "power": float(parts[4]),
                    }
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            log.warning("nvidia-smi not available")
        return info

    def _set_power_mode(self, mode: str):
        thermal_map = {"silent": 0, "balanced": 1, "performance": 2}

        try:
            policy = thermal_map.get(mode)
            if policy is not None:
                subprocess.run(
                    ["bash", "-c", f"echo {policy} | tee /sys/devices/platform/asus-nb-wmi/throttle_thermal_policy > /dev/null"],
                    capture_output=True, timeout=3
                )
            log.info("Requested GPU power mode: %s", mode)
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            log.error("Failed to set GPU mode: %s", e)

    def get_display_info(self) -> dict:
        info = self._get_gpu_info()
        return {
            "value": info.get("usage", 0),
            "unit": "%",
            "title": f"GPU · {self._mode}",
            "details": {
                "temp": info.get("temp", 0),
                "vram_used": info.get("vram_used", 0),
                "vram_total": info.get("vram_total", 0),
                "power": info.get("power", 0),
                "mode": self._mode,
            },
        }