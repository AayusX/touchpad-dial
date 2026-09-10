# Volume Plugin

Controls the system volume.

| Gesture | Action |
|---|---|
| Rotate CW | Volume up (+5%) |
| Rotate CCW | Volume down (−5%) |
| Tap center | Toggle mute |

### Backends (tried in order)

1. uinput `KEY_VOLUMEUP` / `KEY_VOLUMEDOWN` / `KEY_MUTE` (works everywhere)
2. `wpctl set-volume @DEFAULT_SINK@ 5%+` / `5%-` (PipeWire)
3. `pactl` (PulseAudio)