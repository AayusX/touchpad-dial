# Brightness Plugin

Adjusts screen brightness.

| Gesture | Action |
|---|---|
| Rotate CW | Brightness up (+5%) |
| Rotate CCW | Brightness down (−5%) |

### Backends (tried in order)

1. KDE PowerDevil D-Bus (`org.kde.ScreenBrightness.Display.SetBrightness`) —
   reliable on Wayland, no root needed
2. uinput `KEY_BRIGHTNESSUP` / `KEY_BRIGHTNESSDOWN`
3. `brightnessctl`

### Why D-Bus first?

On Wayland, the compositor ignores `KEY_BRIGHTNESS*` coming from a virtual
device. The KDE PowerDevil D-Bus interface is the only path that works reliably
across KDE Plasma sessions.