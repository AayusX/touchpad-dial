# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Settings GUI
- Per-application profiles UI
- Scroll "companion" gesture conversation
- Flatpak / AUR packaging

## [1.0.0] - 2026-09-10

Initial public release.

### Added
- Gesture engine: corner activation, 90°-detent rotation, center tap/hold.
- Exclusive touchpad grab while the dial is active (cursor frozen).
- Circular function picker UI with 2 s auto-fade (selection ring).
- Silent-by-default actions; overlay only on explicit center-hold.
- 7 plugins: Volume, Brightness, Media, Keyboard Backlight, Night Light,
  Screenshot/Recording, GPU mode.
- Plugin architecture with injected `ActionExecutor` for uinput virtual keys.
- Systemd user services for daemon + UI, auto-started on login.
- udev rules + install script for touchpad/I2C/uinput access.
- Debug CLI (`debug.py`) with hardware report and interactive gesture monitor.
- Wayland/X11 aware backends (KDE PowerDevil, KWin NightLight, Spectacle).
- Configurable layout, gesture timing, plugins, themes (default/proart/minimal).

### Fixed
- Rotation events now reach the engine (callback wiring).
- Virtual keys send press **and** release (Wayland needed release).
- Brightness via KDE PowerDevil D-Bus (key events were ignored on Wayland).
- Volume via `wpctl` step syntax (`5%+` / `5%-`).
- Screenshots via `spectacle` on Wayland.

[1.0.0]: https://github.com/AayusX/touchpad-dial/releases/tag/v1.0.0