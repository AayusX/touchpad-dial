# Night Light Plugin

Controls KDE Plasma's built-in Night Light (blue-light filter).

| Gesture | Action |
|---|---|
| Rotate CW | Increase color temperature (warmer, +500K) |
| Rotate CCW | Decrease color temperature (cooler, −500K) |
| Tap center | Toggle Night Light on/off |

Range: 1700 K (very warm) to 6500 K (neutral).

### Backend

KDE D-Bus (`org.kde.KWin.NightLight`):

- `preview(temperature)` — instant live preview while rotating
- `stopPreview()` — revert to the scheduled setting
- `enabled` — read current state

The on/off toggle also persists the `NightColor` group in `kwinrc` via
`kwriteconfig6` and asks KWin to `reconfigure`.

> This plugin is KDE Plasma specific (the D-Bus object lives in KWin). On GNOME
> you'd map this to `org.gnome.SettingsDaemon.Color` instead — a good first
> contribution.