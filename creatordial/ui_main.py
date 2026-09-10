#!/usr/bin/env python3
"""Creator Dial - UI entry point (runs in Wayland session)"""

import sys
import os
import signal
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from creatordial.ui import CreatorDialApp


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
    )


def main():
    parser = argparse.ArgumentParser(description="Creator Dial UI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    logging.getLogger("creatordial.ui").info("Creator Dial UI starting...")

    app = CreatorDialApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
