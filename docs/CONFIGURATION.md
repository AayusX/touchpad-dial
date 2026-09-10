# Configuration

All configuration lives in a single JSON file:

```
~/.config/creatordial/config.json
```

It is created automatically on first install. If you break something, delete
the file and restart the daemon — a fresh default will be written.

## Full reference

```jsonc
{
  "enabled": true,                // Master switch for the dialpad.

  // ---- Gesture timing ----
  "activation_time": 1.0,         // Seconds to hold the corner / center before triggering.
  "rotation_threshold": 90.0,     // Degrees of accumulated rotation per action (detent size).
  "sensitivity": 1.0,             // Multiplies rotation deltas (higher = faster response).

  // ---- Auto-deactivation ----
  "inactivity_timeout": 0,        // Seconds of no touch before deactivation. 0 = never.
  "coactivator_key": "",          // (reserved) keyboard key for co-activation.
  "touchpad_disables_dialpad": true, // (reserved) normal touchpad use deactivates the dial.

  // ---- Gesture zone geometry (touchpad coordinate units) ----
  "layout": {
    "circle_diameter": 1400,          // Diameter of the rotation circle.
    "center_button_diameter": 250,    // Diameter of the center tap/hold circle.
    "circle_center_x": 770,           // X of circle center.
    "circle_center_y": 750,           // Y of circle center.
    "top_right_icon_width": 250,      // Width of the corner activation zone.
    "top_right_icon_height": 250      // Height of the corner activation zone.
  },

  // ---- Plugins ----
  "plugins": {
    "volume":    { "enabled": true, "step": 5 },
    "brightness":{ "enabled": true, "step": 5 },
    "gpu":       { "enabled": true },
    "media":     { "enabled": true },
    "keyboard":  { "enabled": true },
    "screen":    { "enabled": true },
    "nightlight":{ "enabled": true }
  },

  // ---- Appearance ----
  "theme": "default",             // default | proart | minimal (custom themes supported).

  // ---- Diagnostics ----
  "debug": false                  // Verbose logging to journalctl.
}
```

## Tuning tips

### "Rotation feels too fast / slow"

Change `rotation_threshold` and `sensitivity`:

- **Bigger `rotation_threshold`** (e.g. 120) → fewer actions per turn, slower.
- **Smaller** (e.g. 60) → more actions per turn, faster.
- **`sensitivity`** acts as a global multiplier on every rotation step; 0.5
  halves the response, 2.0 doubles it.

### "The circle is off-center on my touchpad"

Every touchpad has different resolution and coordinates. Open the debug tool to
see your touchpad's maximum X/Y:

```bash
~/.local/share/creatordial/.venv/bin/python3 \
  ~/.local/share/creatordial/creatordial/debug.py
```

Look for `max_x` / `max_y`. Then set the layout so the circle is centered on
your touchpad, e.g. for a touchpad with max_x=3880, max_y=2299:

```json
"layout": {
  "circle_diameter": 1400,
  "circle_center_x": 1940,
  "circle_center_y": 1150,
  ...
}
```

### "Hold time feels wrong"

Adjust `activation_time` in seconds. 0.6–0.8 is quicker; 1.2–1.5 is more
deliberate (less accidental activation).

### "I want the dial to switch off automatically"

Set `inactivity_timeout` to e.g. `30` (seconds of no touch before deactivation).

## Per-plugin options

Each plugin entry supports at least `enabled`. Plugins that accept extra keys:

- **volume** — `step`: percent per step (default 5).
- **brightness** — `step`: percent per step (default 5).

## Themes

`theme` selects from the built-in `default`, `proart`, and `minimal` themes.
You can add your own by dropping a JSON theme file in
`~/.config/creatordial/themes/`:

```json
{
  "name": "midnight",
  "displayName": "Midnight",
  "colors": {
    "background": "#1a1d29",
    "centerBackground": "#242838",
    "ringColor": "#a5988a",
    "textPrimary": "#ffffff",
    "textSecondary": "#8894ad",
    "accent": "#4d7cff",
    "border": "#3a4a6b",
    "activeSegment": "#4d7cff"
  },
  "dimensions": { "boxWidth": 300, "boxHeight": 300 },
  "animation": { "fadeSpeed": 0.15, "transitionDuration": 250 },
  "font": { "family": "DejaVu Sans", "weight": "medium" }
}
```

Restart the UI after changing the theme.

## Reloading

After editing `config.json`, restart the services:

```bash
systemctl --user restart creatordial-daemon creatordial-ui
```