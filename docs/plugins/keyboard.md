# Keyboard Backlight Plugin

Controls the keyboard backlight brightness (usually 3 levels on ASUS laptops).

| Gesture | Action |
|---|---|
| Rotate CW | Brightness up |
| Rotate CCW | Brightness down |
| Tap center | Toggle backlight on/off |

### Backends (tried in order)

1. sysfs path `/sys/class/leds/asus::kbd_backlight/brightness` (when writable)
2. uinput `KEY_KBDILLUMUP` / `KEY_KBDILLUMDOWN` / `KEY_KBDILLUMTOGGLE`

> The sysfs file is often root-only; the plugin falls back to virtual keys,
> which the kernel (via `atkbd`/ACPI) turns into real backlight changes on most
> hardware.