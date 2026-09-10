#!/usr/bin/env python3
"""Creator Dial - Debug and diagnostic tool"""

import sys
import os
import time
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from creatordial.core.hardware_detector import HardwareDetector
from creatordial.core.input_reader import InputReader
from creatordial.core.i2c_controller import I2CController


def main():
    parser = argparse.ArgumentParser(description="Creator Dial Debug Tool")
    parser.add_argument("--input", action="store_true", help="Monitor raw input events")
    parser.add_argument("--i2c-test", action="store_true", help="Test I2C connection")
    parser.add_argument("--list-devices", action="store_true", help="List all detected devices")
    args = parser.parse_args()

    print("=" * 60)
    print("  Creator Dial Debug Tool")
    print("=" * 60)
    print()

    detector = HardwareDetector()
    hardware = detector.detect()

    print("HARDWARE INFORMATION")
    print("-" * 40)
    print(f"  Product:    {hardware.product_name}")
    print(f"  Vendor:     {hardware.vendor}")
    print(f"  Board:      {hardware.board_name}")
    print(f"  I2C Bus:    {hardware.i2c_bus}")
    print(f"  I2C Addr:   0x{hardware.i2c_addr:x}")
    print()

    if hardware.touchpad:
        print("TOUCHPAD")
        print("-" * 40)
        print(f"  Name:       {hardware.touchpad.device_name}")
        print(f"  Event ID:   event{hardware.touchpad.event_id}")
        print(f"  Device ID:  {hardware.touchpad.device_id}")
        print(f"  Max X:      {hardware.touchpad.max_x}")
        print(f"  Max Y:      {hardware.touchpad.max_y}")
        print()

    if hardware.dialpad:
        print("DIALPAD")
        print("-" * 40)
        print(f"  Name:       {hardware.dialpad.device_name}")
        print(f"  Event ID:   event{hardware.dialpad.event_id}")
        print(f"  Detected:   {hardware.dialpad.detected}")
        print()

    if hardware.keyboard:
        print("KEYBOARD")
        print("-" * 40)
        print(f"  Name:       {hardware.keyboard.device_name}")
        print(f"  Event ID:   event{hardware.keyboard.event_id}")
        print()

    if args.i2c_test:
        print("I2C TEST")
        print("-" * 40)
        i2c = I2CController(hardware.i2c_bus, hardware.i2c_addr)
        if i2c.test_connection():
            print("  I2C connection: OK")
        else:
            print("  I2C connection: FAILED")
        print()

    if args.input and hardware.touchpad:
        print("INPUT MONITOR (Ctrl+C to stop)")
        print("-" * 40)
        reader = InputReader(hardware.touchpad)

        def on_rotation(direction, magnitude):
            print(f"  ROTATION: {direction} ({magnitude:.1f} degrees)")

        def on_click():
            print("  CLICK")

        def on_double_click():
            print("  DOUBLE CLICK")

        def on_long_press():
            print("  LONG PRESS")

        def on_activation():
            print("  ACTIVATION")

        reader.set_callbacks(
            on_rotation=on_rotation,
            on_click=on_click,
            on_double_click=on_double_click,
            on_long_press=on_long_press,
            on_activation=on_activation,
        )

        if not reader.open():
            print("  Failed to open touchpad device")
            sys.exit(1)

        reader.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            reader.stop()
            print("\n  Monitoring stopped")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
