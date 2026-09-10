# Screenshot / Recording Plugin

Screenshots and screen recording from the center of the dial.

| Gesture | Action |
|---|---|
| Tap center | Take a full-screen screenshot |
| Hold center | Start / stop screen recording |

Screenshots are saved as `~/Pictures/creator_dial_screenshot_<ts>.png`.
Recordings as `~/Pictures/creator_dial_recording_<ts>.mp4`.

### Backends (tried in order)

Screenshot:

1. `spectacle -b -n -o <file>` (KDE, Wayland/X11) — preferred
2. `scrot <file>` (X11)
3. `gnome-screenshot -f <file>`

Recording:

- `wf-recorder -g -f <file>` (Wayland)

> On Wayland, only the compositor's screenshot tool (Spectacle on KDE) can
> capture the full screen. `scrot` still works on X11 sessions.