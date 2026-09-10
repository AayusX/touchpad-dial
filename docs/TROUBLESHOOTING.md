# Troubleshooting

## Where the logs are

Both services log to the user journal:

```bash
# Live follow of both services
journalctl --user -f -u creatordial-daemon -u creatordial-ui

# Last 200 lines, all levels
journalctl --user -u creatordial-daemon --no-pager -n 200

# Debug detail
journalctl --user -u creatordial-daemon --no-pager -n 200 -l | grep DEBUG
```

Run the daemon with debug logging on in config:

```json
{ "debug": true }
```

then restart:

```bash
systemctl --user restart creatordial-daemon
```

## The dial does nothing when I rotate

1. **Is the dial active?** The touchpad must first be activated by holding the
   **top-right corner** for ~1 s. Check the log:
   ```bash
   journalctl --user -u creatordial-daemon --since "5 minutes ago"
   ```
   Look for `DialPad activated` / `Touchpad grabbed`.

2. **Check the layout zone.** Your touchpad's coordinates may differ from the
   defaults. Run:
   ```bash
   ~/.local/share/creatordial/.venv/bin/python3 \
     ~/.local/share/creatordial/creatordial/debug.py
   ```
   Confirm the circle center matches your touchpad's max X/Y, see
   [Configuration → tuning](CONFIGURATION.md#the-circle-is-off-center-on-my-touchpad).

3. **Watch it live.** `debug.py` has an interactive input mode:
   ```bash
   ~/.local/share/creatordial/.venv/bin/python3 \
     ~/.local/share/creatordial/creatordial/debug.py --input
   ```
   Rotate and confirm `Rotation CW/CCW` lines appear.

## The touchpad/cursor is frozen and won't react

The daemon grabbed the touchpad exclusively. That ends when the dial
deactivates *or* the daemon exits. To recover:

```bash
systemctl --user restart creatordial-daemon
```

If it ever hung, the kernel releases grabs automatically when the process dies
(its fd closes), so a full crash also unfreezes the touchpad.

## A plugin does nothing in particular

Each plugin has multiple backends; a missing backend just means it falls back.

| Plugin | Preferred backend | Fallbacks |
|---|---|---|
| Volume | D-Bus / `wpctl` | `pactl`, `amixer`, uinput keys |
| Brightness | KDE PowerDevil D-Bus | `brightnessctl`, uinput keys, sysfs |
| Media | uinput transport keys | `playerctl` |
| Keyboard | sysfs path | uinput `KEY_KBDILLUM*` |
| Screen | `spectacle` (KDE) | `scrot`, `gnome-screenshot`; record via `wf-recorder` |
| Night Light | KDE `org.kde.KWin.NightLight` D-Bus | — (KDE only) |
| GPU | `nvidia-smi` (read) | **power-mode switch needs root** (sysfs) |

Common specifics:

- **Night Light**: requires **KDE Plasma** (the D-Bus object is owned by KWin).
- **Keyboard backlight**: needs your `/sys/class/leds/asus::kbd_backlight`
  path; the plugin falls back to virtual keys otherwise.
- **GPU mode switch**: writing the thermal policy sysfs file
  (`/sys/devices/platform/asus-nb-wmi/throttle_thermal_policy`) requires root.
  The plugin reports GPU utilization regardless.
- **Screenshot**: on Wayland, only KDE's `spectacle` can capture
  full-screen; `scrot` needs X11.

## I hold the corner but it never activates

- Increase `activation_time` isn't the issue — check you're inside the corner
  **zone**. On very high-resolution touchpads the default 250×250 box may be
  small; enlarge `layout.top_right_icon_width/height` or recenter the layout.

## The UI overlay doesn't appear

Check the socket is healthy:

```bash
ls -l /tmp/creatordial.sock        # should exist while UI runs
systemctl --user status creatordial-ui
```

Restart the UI if it's stale:

```bash
systemctl --user restart creatordial-ui
```

## Nothing starts at login

Confirm the services are enabled:

```bash
systemctl --user is-enabled creatordial-daemon creatordial-ui
systemctl --user enable creatordial-daemon creatordial-ui
```

Also make sure you're inside a graphical session (the services target
`graphical-session.target`).

## Permissions errors

If you see `Permission denied` opening `/dev/input/event*` or `/dev/i2c-*`:

1. Re-run `./install.sh` (it adds the groups + udev rules).
2. **Log out and back in** so group membership applies.
3. Verify:
   ```bash
   groups                # must include input, i2c, uinput
   ls -l /dev/input/     # devices group "input"
   ```

## I get a traceback in the journal, can I report it?

Yes — please open a GitHub issue with the **full traceback** (last ~50 lines)
and the output of:

```bash
~/.local/share/creatordial/.venv/bin/python3 \
  ~/.local/share/creatordial/creatordial/debug.py
```

Bugs are label `bug`, feature ideas `enhancement`.
[Issue templates](https://github.com/AayusX/touchpad-dial/issues/new/choose).