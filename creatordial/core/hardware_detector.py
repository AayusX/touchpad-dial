import os
import re
import subprocess
import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("creatordial.hardware")


@dataclass
class TouchpadInfo:
    event_id: str
    device_name: str
    device_id: str
    device_addr: int
    sysfs_path: str
    min_x: int = 0
    max_x: int = 4096
    min_y: int = 0
    max_y: int = 4096


@dataclass
class DialPadInfo:
    event_id: str
    device_name: str
    detected: bool = False


@dataclass
class KeyboardInfo:
    event_id: str
    device_name: str


@dataclass
class HardwareProfile:
    product_name: str
    vendor: str
    board_name: str
    touchpad: Optional[TouchpadInfo] = None
    dialpad: Optional[DialPadInfo] = None
    keyboard: Optional[KeyboardInfo] = None
    i2c_bus: int = 1
    i2c_addr: int = 0x15

    @property
    def has_dialpad(self) -> bool:
        return self.dialpad is not None and self.dialpad.detected


TOUCHPAD_PREFIXES = ("ASUE", "ELAN", "ASUP", "ASUF", "ASCE", "ASCF", "ASCP")
DIALPAD_SUFFIXES = ("DialPad", "dialpad")
KEYBOARD_NAMES = ("AT Translated Set 2 keyboard",)
KEYBOARD_ASUS_NAMES = ("ASUE", "Asus", "ASUP", "ASUF")


class HardwareDetector:
    def __init__(self):
        self._profile: Optional[HardwareProfile] = None

    def detect(self) -> HardwareProfile:
        product_name = self._read_dmi("product_name")
        vendor = self._read_dmi("sys_vendor")
        board_name = self._read_dmi("board_name")

        self._profile = HardwareProfile(
            product_name=product_name or "Unknown",
            vendor=vendor or "Unknown",
            board_name=board_name or "Unknown",
        )

        self._detect_input_devices()
        self._detect_i2c_bus()

        log.info(
            "Hardware: %s | Touchpad: %s | DialPad: %s | Keyboard: %s",
            product_name,
            self._profile.touchpad.event_id if self._profile.touchpad else "None",
            self._profile.dialpad.event_id if self._profile.dialpad else "None",
            self._profile.keyboard.event_id if self._profile.keyboard else "None",
        )

        return self._profile

    @staticmethod
    def _read_dmi(field_name: str) -> Optional[str]:
        path = f"/sys/devices/virtual/dmi/id/{field_name}"
        try:
            with open(path) as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None

    def _detect_input_devices(self):
        try:
            with open("/proc/bus/input/devices") as f:
                content = f.read()
        except FileNotFoundError:
            log.error("Cannot read /proc/bus/input/devices")
            return

        blocks = content.split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue

            name_line = next((l for l in lines if l.startswith("N: Name=")), None)
            handler_line = next((l for l in lines if l.startswith("H: Handlers=")), None)
            sysfs_line = next((l for l in lines if l.startswith("S: Sysfs=")), None)

            if not name_line or not handler_line:
                continue

            name = name_line.split('"')[1] if '"' in name_line else ""
            handlers = handler_line.split("Handlers=")[1].strip()

            event_id = self._extract_event_id(handlers)

            if any(name.startswith(p) for p in TOUCHPAD_PREFIXES) and "Touchpad" in name:
                device_id = ""
                if sysfs_line:
                    m = re.search(r"i2c-(\d+)", sysfs_line)
                    if m:
                        device_id = m.group(1)

                addr = 0x38 if ("ASUF1416" in name or "ASUF1205" in name or "ASUF1204" in name) else 0x15

                self._profile.touchpad = TouchpadInfo(
                    event_id=event_id,
                    device_name=name,
                    device_id=device_id,
                    device_addr=addr,
                    sysfs_path=sysfs_line.split("Sysfs=")[1].strip() if sysfs_line else "",
                )
                self._detect_touchpad_dimensions(event_id)

            elif any(name.startswith(p) for p in KEYBOARD_NAMES) or (
                any(name.startswith(p) for p in KEYBOARD_ASUS_NAMES) and "Keyboard" in name
            ):
                self._profile.keyboard = KeyboardInfo(
                    event_id=event_id,
                    device_name=name,
                )

            elif "DialPad" in name or "dialpad" in name.lower():
                self._profile.dialpad = DialPadInfo(
                    event_id=event_id,
                    device_name=name,
                    detected=True,
                )

        if self._profile.touchpad is None:
            log.warning("No compatible touchpad found")
        if self._profile.dialpad is None:
            log.warning("DialPad virtual device not detected (may appear after I2C activation)")

    def _detect_touchpad_dimensions(self, event_id: str):
        max_x = max_y = None

        dev_path = f"/sys/class/input/event{event_id}/device"
        try:
            abs_x_max = self._read_sysfs(dev_path, "abs_x_max")
            abs_y_max = self._read_sysfs(dev_path, "abs_y_max")
            max_x = int(abs_x_max) if abs_x_max else None
            max_y = int(abs_y_max) if abs_y_max else None
        except (ValueError, TypeError):
            pass

        if max_x is None or max_y is None:
            try:
                from libevdev import Device, EV_ABS

                with open(f"/dev/input/event{event_id}", "rb") as fd:
                    dev = Device(fd)
                    abs_x = dev.absinfo[EV_ABS.ABS_X]
                    abs_y = dev.absinfo[EV_ABS.ABS_Y]
                    max_x = max_x or abs_x.maximum
                    max_y = max_y or abs_y.maximum
            except Exception:
                max_x = max_x or 4096
                max_y = max_y or 4096

        if self._profile.touchpad:
            self._profile.touchpad.max_x = max_x
            self._profile.touchpad.max_y = max_y
        log.info(
            "Touchpad dimensions: %d x %d",
            self._profile.touchpad.max_x if self._profile.touchpad else 0,
            self._profile.touchpad.max_y if self._profile.touchpad else 0,
        )

    @staticmethod
    def _read_sysfs(base_path: str, filename: str) -> Optional[str]:
        path = os.path.join(base_path, filename)
        try:
            with open(path) as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None

    @staticmethod
    def _extract_event_id(handlers_str: str) -> str:
        m = re.search(r"event(\d+)", handlers_str)
        return m.group(1) if m else ""

    def _detect_i2c_bus(self):
        if not self._profile.touchpad or not self._profile.touchpad.device_id:
            log.warning("Cannot detect I2C bus without touchpad device_id")
            return

        bus_num = self._profile.touchpad.device_id
        self._profile.i2c_bus = int(bus_num) if bus_num.isdigit() else 1

        for addr in [0x15, 0x38]:
            path = f"/dev/i2c-{self._profile.i2c_bus}"
            if os.path.exists(path):
                try:
                    cmd = ["i2ctransfer", "-f", "-y", str(self._profile.i2c_bus),
                           f"w13@0x{addr:x}", "0x05", "0x00", "0x3d", "0x03", "0x06", "0x00",
                           "0x07", "0x00", "0x0d", "0x14", "0x03", "0x00", "0xad"]
                    subprocess.run(cmd, capture_output=True, timeout=2)
                    self._profile.i2c_addr = addr
                    log.info("I2C device found at bus %s addr 0x%x", self._profile.i2c_bus, addr)
                    return
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue

    def test_dialpad_activation(self) -> bool:
        if not self._profile or not self._profile.touchpad:
            return False

        bus = self._profile.i2c_bus
        addr = self._profile.i2c_addr

        try:
            activate_cmd = [
                "i2ctransfer", "-f", "-y", str(bus),
                f"w13@0x{addr:x}",
                "0x05", "0x00", "0x3d", "0x03", "0x06", "0x00",
                "0x07", "0x00", "0x0d", "0x14", "0x03", "0x01", "0xad",
            ]
            subprocess.run(activate_cmd, capture_output=True, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
