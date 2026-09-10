# Media Plugin

Controls media transport for whatever player is currently playing.

| Gesture | Action |
|---|---|
| Rotate CW | Next track |
| Rotate CCW | Previous track |
| Tap center | Play / pause |
| Hold center | Next track |

### Backends (tried in order)

1. uinput media keys (`KEY_NEXTSONG`, `KEY_PREVIOUSSONG`, `KEY_PLAYPAUSE`) —
   works with GNOME MediaKeys, KDE, and most players
2. `playerctl next/previous/play-pause` (MPRIS)