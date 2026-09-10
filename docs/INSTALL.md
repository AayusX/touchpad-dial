# Installation

This guide covers installing Touchpad Dial on a Debian/Ubuntu-based Linux system.

## Requirements

- **Linux** (Debian/Ubuntu preferred; other distros need equivalent packs)
- **Python 3.10+** with `python3-venv` and `python3-pip`
- A **multi-touch touchpad** (virtually all modern laptops qualify)
- `systemd` (for the auto-start services)

> The daemon needs to read raw touchpad input, use `uinput`, and optionally talk
> to I2C. The installer sets up the required udev rules and user groups for you.

## 1. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Optional but recommended for full functionality:

```bash
# Volume fallbacks
sudo apt install -y pipewire-pulse pulseaudio-utils
# Night light via KDE (or use the bundled D-Bus integration)
sudo apt install -y qdbus-qt6
# Screenshots (KDE): already present on Plasma; scrot as a fallback
sudo apt install -y scrot
# GPU info
sudo apt install -y nvidia-utils-535
```

## 2. Install Touchpad Dial

```bash
git clone https://github.com/AayusX/touchpad-dial.git
cd touchpad-dial
./install.sh
```

The installer:

1. Verifies system dependencies.
2. Detects your hardware and touchpad.
3. Creates `~/.local/share/creatordial` (app) and `~/.config/creatordial` (config).
4. Creates a Python virtual environment and installs dependencies.
5. Copies the application files.
6. Adds your user to the `input`, `i2c`, and `uinput` groups.
7. Installs udev rules for touchpad, DialPad, and I2C access.
8. Installs and enables the two systemd user services.
9. Writes a default configuration if none exists.

## 3. Finish up

**Log out and back in** (or reboot) so the group changes take effect — this is
required to read `/dev/input/event*` and `/dev/i2c-*`.

After logging back in, confirm everything is running:

```bash
systemctl --user status creatordial-daemon creatordial-ui
```

Both should show `Active: active (running)`.

## 4. Manual start / stop

```bash
systemctl --user start creatordial-daemon creatordial-ui   # start now
systemctl --user stop creatordial-daemon creatordial-ui    # stop now
systemctl --user restart creatordial-daemon creatordial-ui # restart
```

The services are enabled by default, so they start automatically with your
desktop session. To disable auto-start:

```bash
systemctl --user disable creatordial-daemon creatordial-ui
```

## 5. Verify gestures

Run the debug CLI to confirm the daemon can read your touchpad:

```bash
~/.local/share/creatordial/.venv/bin/python3 \
  ~/.local/share/creatordial/creatordial/debug.py
```

You should see your touchpad detected with its event device (e.g. `event5`),
maximum coordinates, and — on compatible ASUS hardware — the DialPad I2C address.

Then try the dial (see [Usage](USAGE.md)).

## Uninstalling

```bash
cd touchpad-dial
./install.sh --uninstall
```

This stops/disables the services, removes the app files and udev rules, but
**keeps your configuration** at `~/.config/creatordial` so a reinstall keeps
your settings.

## Installing on other distributions

The concepts are the same; the package names differ:

| Distro | Install | udev | Notes |
|---|---|---|---|
| Fedora | `dnf install python3-devel python3-pip` | `/etc/udev/rules.d/` | venv works the same |
| Arch | `pacman -S python python-pip` | `/usr/lib/udev/rules.d/` | see `install.sh` paths |
| openSUSE | `zypper install python3 python3-pip` | `/usr/lib/udev/rules.d/` | |

The installer is Debian-flavoured; on other distros you can run the steps
manually using the paths printed in `install.sh`. Contributions to make the
installer portable are welcome.