import subprocess
import logging
import json
from typing import Optional, Any

from libevdev import EV_KEY, EV_REL, EV_SYN, Device, InputEvent

log = logging.getLogger("creatordial.executor")


class ActionExecutor:
    def __init__(self):
        self._virtual_device: Optional[Device] = None
        self._udev = None

    def initialize_virtual_device(self, name: str = "Creator Dial Virtual Device"):
        try:
            self._virtual_device = Device()
            self._virtual_device.name = name
            self._virtual_device.enable(EV_KEY.KEY_VOLUMEUP)
            self._virtual_device.enable(EV_KEY.KEY_VOLUMEDOWN)
            self._virtual_device.enable(EV_KEY.KEY_MUTE)
            self._virtual_device.enable(EV_KEY.KEY_BRIGHTNESSUP)
            self._virtual_device.enable(EV_KEY.KEY_BRIGHTNESSDOWN)
            self._virtual_device.enable(EV_KEY.KEY_PLAYPAUSE)
            self._virtual_device.enable(EV_KEY.KEY_NEXTSONG)
            self._virtual_device.enable(EV_KEY.KEY_PREVIOUSSONG)
            self._virtual_device.enable(EV_KEY.KEY_MEDIA)
            self._virtual_device.enable(EV_KEY.KEY_KBDILLUMUP)
            self._virtual_device.enable(EV_KEY.KEY_KBDILLUMDOWN)
            self._virtual_device.enable(EV_KEY.KEY_KBDILLUMTOGGLE)
            self._virtual_device.enable(EV_REL.REL_WHEEL)
            self._virtual_device.enable(EV_REL.REL_WHEEL_HI_RES)

            self._udev = self._virtual_device.create_uinput_device()
            log.info("Virtual device initialized: %s", name)
        except Exception as e:
            log.error("Failed to initialize virtual device: %s", e)

    def send_key(self, keycode, value: int = 1):
        if not self._udev:
            log.error("Virtual device not initialized")
            return

        try:
            if value == 1:
                self._udev.send_events([
                    InputEvent(EV_SYN.SYN_REPORT, 0),
                    InputEvent(keycode, 1),
                    InputEvent(EV_SYN.SYN_REPORT, 0),
                    InputEvent(keycode, 0),
                    InputEvent(EV_SYN.SYN_REPORT, 0),
                ])
            else:
                self._udev.send_events([
                    InputEvent(EV_SYN.SYN_REPORT, 0),
                    InputEvent(keycode, value),
                    InputEvent(EV_SYN.SYN_REPORT, 0),
                    InputEvent(keycode, 0),
                    InputEvent(EV_SYN.SYN_REPORT, 0),
                ])
        except Exception as e:
            log.error("Failed to send key event: %s", e)

    def send_key_combo(self, keys: list):
        if not self._udev:
            log.error("Virtual device not initialized")
            return

        try:
            events = []
            for key in keys:
                events.append(InputEvent(key, 1))
                events.append(InputEvent(EV_SYN.SYN_REPORT, 0))
            for key in reversed(keys):
                events.append(InputEvent(key, 0))
                events.append(InputEvent(EV_SYN.SYN_REPORT, 0))

            self._udev.send_events(events)
        except Exception as e:
            log.error("Failed to send key combo: %s", e)

    def send_scroll(self, direction: int, amount: int = 120):
        if not self._udev:
            log.error("Virtual device not initialized")
            return

        try:
            self._udev.send_events([
                InputEvent(EV_REL.REL_WHEEL, direction),
                InputEvent(EV_REL.REL_WHEEL_HI_RES, direction * amount),
                InputEvent(EV_SYN.SYN_REPORT, 0),
            ])
        except Exception as e:
            log.error("Failed to send scroll: %s", e)

    def execute_command(self, command: str) -> Optional[str]:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            log.error("Command failed: %s -> %s", command, result.stderr.strip())
        except subprocess.TimeoutExpired:
            log.error("Command timed out: %s", command)
        except Exception as e:
            log.error("Command error: %s -> %s", command, e)
        return None

    def execute_action(self, action: dict):
        action_type = action.get("type", "")

        if action_type == "key":
            self.send_key(action["keycode"])

        elif action_type == "key_combo":
            self.send_key_combo(action["keys"])

        elif action_type == "scroll":
            self.send_scroll(action.get("direction", 1), action.get("amount", 120))

        elif action_type == "command":
            self.execute_command(action["command"])

        elif action_type == "volume_up":
            self.send_key(EV_KEY.KEY_VOLUMEUP)

        elif action_type == "volume_down":
            self.send_key(EV_KEY.KEY_VOLUMEDOWN)

        elif action_type == "mute":
            self.send_key(EV_KEY.KEY_MUTE)

        elif action_type == "brightness_up":
            self.send_key(EV_KEY.KEY_BRIGHTNESSUP)

        elif action_type == "brightness_down":
            self.send_key(EV_KEY.KEY_BRIGHTNESSDOWN)

        elif action_type == "play_pause":
            self.send_key(EV_KEY.KEY_PLAYPAUSE)

        elif action_type == "next_track":
            self.send_key(EV_KEY.KEY_NEXTSONG)

        elif action_type == "prev_track":
            self.send_key(EV_KEY.KEY_PREVIOUSSONG)

        elif action_type == "media":
            self.send_key(EV_KEY.KEY_MEDIA)

        else:
            log.warning("Unknown action type: %s", action_type)

    def cleanup(self):
        if self._udev:
            try:
                import os
                dev_path = f"/dev/uinput"
                if os.path.exists(dev_path):
                    pass
            except Exception:
                pass
        self._udev = None
        self._virtual_device = None
