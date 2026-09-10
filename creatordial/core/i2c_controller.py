import subprocess
import logging
from typing import Optional

from periphery import I2C

log = logging.getLogger("creatordial.i2c")


class I2CController:
    def __init__(self, bus: int, addr: int):
        self.bus = bus
        self.addr = addr
        self.device_path = f"/dev/i2c-{bus}"
        self._available = True

    def _send_raw(self, data: list[int]) -> bool:
        hex_data = [f"0x{b:02x}" for b in data]
        cmd = [
            "i2ctransfer", "-f", "-y", str(self.bus),
            f"w{len(data)}@0x{self.addr:x}",
        ] + hex_data

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            log.debug("i2ctransfer failed: %s, trying python-periphery", e)

        try:
            with I2C(self.device_path) as i2c:
                msg = I2C.Message(data)
                i2c.transfer(self.addr, [msg])
                return True
        except Exception as e:
            log.error("I2C transfer failed: %s", e)
            self._available = False
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def activate_dialpad(self) -> bool:
        unlock_data = [
            0x05, 0x00, 0x3d, 0x03, 0x06, 0x00,
            0x07, 0x00, 0x0d, 0x14, 0x03, 0x60, 0xad,
        ]
        activate_data = [
            0x05, 0x00, 0x3d, 0x03, 0x06, 0x00,
            0x07, 0x00, 0x0d, 0x14, 0x03, 0x01, 0xad,
        ]

        if self._send_raw(unlock_data) and self._send_raw(activate_data):
            log.info("DialPad activated")
            return True
        return False

    def deactivate_dialpad(self) -> bool:
        lock_data = [
            0x05, 0x00, 0x3d, 0x03, 0x06, 0x00,
            0x07, 0x00, 0x0d, 0x14, 0x03, 0x61, 0xad,
        ]
        deactivate_data = [
            0x05, 0x00, 0x3d, 0x03, 0x06, 0x00,
            0x07, 0x00, 0x0d, 0x14, 0x03, 0x00, 0xad,
        ]

        if self._send_raw(lock_data) and self._send_raw(deactivate_data):
            log.info("DialPad deactivated")
            return True
        return False

    def set_led_state(self, value_hex: str) -> bool:
        data = [
            0x05, 0x00, 0x3d, 0x03, 0x06, 0x00,
            0x07, 0x00, 0x0d, 0x14, 0x03, int(value_hex, 16), 0xad,
        ]
        return self._send_raw(data)

    def test_connection(self) -> bool:
        return self.set_led_state("0x00")
