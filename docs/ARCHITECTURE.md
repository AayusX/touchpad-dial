# Architecture

Touchpad Dial is a **two-process system**: a headless **daemon** that reads the
touchpad and runs plugins, and a **UI** process that draws the overlay. They
talk over a Unix socket.

```
┌──────────────────────────────────┐            ┌──────────────────────────────────┐
│       creatordial-daemon          │            │         creatordial-ui           │
│                                  │            │                                  │
│  ┌────────────────────────────┐  │  JSON via  │  ┌────────────────────────────┐  │
│  │       DialEngine            │  │  datagrams │  │      SocketReader          │  │
│  │  (orchestrator / state)     │──┼──────────►│  │  /tmp/creatordial.sock     │  │
│  └─────┬──────────┬───────────┘  │  socket    │  └────────────┬───────────────┘  │
│        │          │              │            │               │                  │
│  ┌─────▼─────┐ ┌──▼─────────┐    │            │       ┌───────▼──────────────┐   │
│  │InputReader│ │Plugins     │    │            │       │     DialWidget       │   │
│  │(libevdev) │ │(7 built-in)│    │            │       │  QPainter ring/circle│   │
│  └─────┬─────┘ └──┬─────────┘    │            │       │  fade + auto-hide    │   │
│        │          │              │            │       └──────────────────────┘   │
│        │     ┌────▼─────┐       │            │                                  │
│        │     │ActionExec│       │            │       ┌──────────────────────┐   │
│        │     │uinput +  │       │            │       │   SystemTrayIcon     │   │
│        │     │subprocess│       │            │       └──────────────────────┘   │
│        ▼     └──────────┘       │            │                                  │
│  [touchpad]                     │            │                                  │
│  /dev/input/eventN              │            │                                  │
└──────────────────────────────────┘            └──────────────────────────────────┘
```

## Processes & IPC

### The daemon (`creatordial-daemon.service`)

Owns all the logic. Started automatically at login. Key components:

| Component | File | Responsibility |
|---|---|---|
| `DialEngine` | `core/engine.py` | Orchestrator: activation state, plugin routing, gesture callbacks |
| `InputReader` | `core/input_reader.py` | Reads raw multi-touch events via `libevdev`; produces gestures |
| `GestureEngine` | `core/gesture_engine.py` | Normalizes gestures into `GestureEvent`s |
| `PluginManager`-ish | `engine.register_plugin()` | Holds registered plugins, injects the executor |
| `ActionExecutor` | `core/action_executor.py` | Emits virtual keys (uinput), runs CLI commands, sends scroll |
| `I2CController` | `core/i2c_controller.py` | Unlock/activate the ASUS touchpad hardware dialpad EC |
| `UIIPCServer` | `core/ui_ipc.py` | Sends JSON messages to the UI socket |
| `WindowTracker` | `core/window_tracker.py` | Detects the focused app for per-app profiles |
| `HardwareDetector` | `core/hardware_detector.py` | Finds touchpad, event node, I2C bus/address |

### The UI (`creatordial-ui.service`)

Pure presentation. Reads JSON from the socket and renders.

| Component | File | Responsibility |
|---|---|---|
| `SocketReader` | `ui/__init__.py` | Binds `/tmp/creatordial.sock`, polls (30 ms) with a `QTimer` |
| `DialWidget` | `ui/__init__.py` | Frameless translucent overlay; draws ring, segments, center |
| `CreatorDialApp` | `ui/__init__.py` | `QApplication` + tray icon + menu |

## IPC protocol

- **Transport:** Unix domain socket, `SOCK_DGRAM` (unreliable datagrams — fine
  for UI hints).
- **Path:** `/tmp/creatordial.sock` (UI owns the bind; daemon only sends).
- **Format:** newline-delimited JSON objects.

Message shapes sent by the daemon:

```jsonc
// Selection mode entered (center-hold) — UI shows the segmented ring
{ "mode": "selection", "titles": ["Volume", "Brightness", ...],
  "icons": ["audio-volume-high", ...], "title": "Volume" }

// Selected plugin changed (rotation while holding, or center tap)
{ "title": "Brightness", "value": 63, "unit": "%" }

// Selection finished — fade out
{ "mode": "done" }
```

## Event flow (a single rotation)

1. Kernel delivers `ABS_MT_POSITION_X/Y` + `BTN_TOOL_FINGER` to `/dev/input/eventN`.
2. `InputReader` thread (libevdev `Device.events()`) tracks finger state and
   computes the touch position relative to the layout zones.
3. On rotation in the circle zone, `_process_rotation` accumulates angle deltas
   (`atan2` based, with wraparound handling); when `|accumulated| >=
   rotation_threshold` it fires `on_rotation(direction, magnitude)`.
4. `DialEngine._gesture_rotation` wraps it in a `GestureEvent` and emits through
   `GestureEngine`.
5. The engine calls the current plugin's `execute(direction, magnitude)`.
6. The plugin returns `{value, unit, title}`; the engine sends it to the UI
   socket for display and performs the system action (uinput keys, D-Bus, CLI).
7. The UI draws/updates the overlay (or stays silent for normal rotation).

## Activation & grab

When the corner-hold gesture completes (`on_activation`):

1. `I2CController` sends the ASUS touchpad EC "unlock + activate" command
   (`i2ctransfer`, bus/address from `HardwareDetector`, typically `0x15`).
2. `InputReader.grab()` performs an exclusive **libevdev grab** of the touchpad,
   freezing the cursor — mistakes in the middle of rotation are impossible.
3. On `on_deactivation`, the EC is put back and `ungrab()` re-enables the mouse.

If the daemon exits unexpectedly, the kernel releases the grab automatically
(fd close), so the touchpad never stays stuck.

## Gesture recognition details

- **Angle:** `(atan2(dy, dx) * 180/π + 90) % 360`, so "up" = 0°.
- **Delta:** signed shortest-arc between consecutive samples (wraparound-safe).
- **Accumulate:** `delta × sensitivity` added to `angle_accumulator`.
- **Fire:** once `|accumulator| ≥ rotation_threshold`, emit one event and reset.
- **Center tap** = press+release in the center circle lasting < 0.3 s.
- **Center hold** = finger held ≥ `activation_time` in the center circle →
  selection mode; release confirms.

## Per-app profiles

`WindowTracker` polls the focused window (X11 via `xdotool`, KDE via `qdbus`,
GNOME via `gdbus`, Sway/Hyprland via `swaymsg`/`hyprctl`). Profiles match the
foreground binary/title against configurable rules and can rebind plugins per
app. See `creatordial/profiles.py` and the `WindowTracker` module.

## Key libraries

| Library | Used for |
|---|---|
| `libevdev` | Reading raw touchpad events |
| `uinput` (via libevdev) | Virtual input device for system keys |
| `PySide6 / Qt 6` | Overlay UI, animation, tray |
| `python-periphery` | I2C access (fallback path) |
| D-Bus (`busctl`/`qdbus6`/`gdbus`) | KDE PowerDevil brightness, KWin NightLight |

## File map

```
creatordial/
├── daemon.py                 # entry point (systemd)
├── ui_main.py                # UI entry point (systemd)
├── debug.py                  # CLI diagnostics
├── config.py                 # config.json load/validation
├── profiles.py               # per-app profiles
├── themes.py                 # theme definitions
├── core/
│   ├── engine.py             # DialEngine orchestration
│   ├── input_reader.py       # libevdev → gestures
│   ├── gesture_engine.py     # gesture normalization
│   ├── action_executor.py    # uinput / CLI actions
│   ├── i2c_controller.py     # ASUS EC activation
│   ├── ui_ipc.py             # daemon→UI messages
│   ├── dbus_server.py        # (reserved) D-Bus service
│   ├── window_tracker.py     # focused-app detection
│   └── hardware_detector.py  # device discovery
└── plugins/
    ├── __init__.py           # BasePlugin contract
    ├── volume/               # volume plugin
    ├── brightness/           # brightness plugin
    ├── gpu/                  # GPU mode plugin
    ├── media/                # media transport plugin
    ├── keyboard/             # keyboard backlight plugin
    ├── screen/               # screenshot/record plugin
    └── nightlight/           # KDE night light plugin
```