#!/usr/bin/env python3
"""Creator Dial - Main entry point for the core engine (daemon mode)"""

import sys
import os
import signal
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from creatordial.core.engine import DialEngine
from creatordial.config import ConfigManager
from creatordial.profiles import ProfileManager
from creatordial.plugins.volume import VolumePlugin
from creatordial.plugins.brightness import BrightnessPlugin
from creatordial.plugins.gpu import GPUPlugin
from creatordial.plugins.media import MediaPlugin
from creatordial.plugins.keyboard import KeyboardPlugin
from creatordial.plugins.screen import ScreenPlugin
from creatordial.plugins.nightlight import NightLightPlugin


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
    )


def main():
    parser = argparse.ArgumentParser(description="Creator Dial Core Engine")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--no-plugins", action="store_true", help="Start without plugins")
    args = parser.parse_args()

    setup_logging(args.debug)
    log = logging.getLogger("creatordial.main")

    log.info("Creator Dial v1.0.0 starting...")

    config_mgr = ConfigManager(args.config)
    config = config_mgr.load()

    engine = DialEngine(config)

    log.info("Detecting hardware...")
    hardware = engine.detect_hardware()

    if not hardware.touchpad:
        log.error("No compatible touchpad found. Exiting.")
        sys.exit(1)

    if not hardware.has_dialpad:
        log.warning("DialPad virtual device not detected. Attempting I2C activation...")

    if not args.no_plugins:
        log.info("Loading plugins...")
        engine.register_plugin("volume", VolumePlugin())
        engine.register_plugin("brightness", BrightnessPlugin())
        engine.register_plugin("gpu", GPUPlugin())
        engine.register_plugin("media", MediaPlugin())
        engine.register_plugin("keyboard", KeyboardPlugin())
        engine.register_plugin("screen", ScreenPlugin())
        engine.register_plugin("nightlight", NightLightPlugin())

    log.info("Loading profiles...")
    profile_mgr = ProfileManager()
    profile_mgr.load_profiles()
    engine.load_profiles(profile_mgr.get_all_profiles())

    log.info("Starting engine...")
    if not engine.start():
        log.error("Failed to start engine. Exiting.")
        sys.exit(1)

    log.info("Creator Dial is running. Press Ctrl+C to stop.")

    def signal_handler(sig, frame):
        log.info("Shutting down...")
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down...")
        engine.stop()


if __name__ == "__main__":
    main()
