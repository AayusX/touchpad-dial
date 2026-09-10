# Plugin Development

Plugins are the heart of Touchpad Dial. Each plugin maps the dial's four
gestures (`clockwise`, `counterclockwise`, `click`, `long_press`) to a system
action. This guide shows you how to write one in ~10 minutes.

## The contract

Every plugin subclasses `BasePlugin` from `creatordial/plugins/__init__.py`:

```python
class BasePlugin(ABC):
    name: str            # internal id, e.g. "volume"
    icon: str            # freedesktop icon name for the UI
    display_name: str    # human label shown on the ring

    @abstractmethod
    def execute(self, direction: str, magnitude: float = 0) -> dict | None: ...
    # directions: "clockwise" | "counterclockwise" | "click" | "long_press"

    def set_executor(self, executor): ...   # injected uinput/virtual-key engine
    def configure(self, config: dict): ...  # called on profile/config apply
    def get_display_info(self) -> dict: ... # {value, title} for the UI
    def get_status(self) -> dict: ...       # {name, display_name, value}
```

## Minimal example

```python
# creatordial/plugins/mute/__init__.py
import subprocess
from .. import BasePlugin

class MutePlugin(BasePlugin):
    name = "mute"
    icon = "audio-volume-muted"
    display_name = "Mute"

    def execute(self, direction, magnitude=0):
        if direction in ("click", "long_press"):
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_SINK@", "toggle"])
        return {"value": "toggled", "title": self.display_name}
```

## Emitting system keys via the executor

Instead of shelling out, plugins can synthesize real key events through the
injected `ActionExecutor`. Keys are `libevdev.EV_KEY` constants:

```python
from libevdev import EV_KEY

class MutePlugin(BasePlugin):
    def set_executor(self, executor):
        self._executor = executor

    def execute(self, direction, magnitude=0):
        if self._executor:
            self._executor.send_key(EV_KEY.KEY_MUTE)
        return {"value": 50, "unit": "%", "title": self.display_name}
```

`send_key` handles press **and** release — essential for the Wayland compositor
to notice the key. `ActionExecutor` also exposes `send_scroll(delta)` and
`execute_command(...)` (used by the GPU/profile paths).

## Registering your plugin

In `creatordial/daemon.py`:

```python
from creatordial.plugins.mute import MutePlugin

engine.register_plugin("mute", MutePlugin())
```

And optionally add an `enabled` toggle + defaults in the config (see
[Configuration](CONFIGURATION.md)). The UI picks up the new entry
automatically via the selection-ring message.

## Display data

`execute()` may return:

```python
{"value": 63, "unit": "%", "title": "Volume"}
```

- `value` — the headline number/string.
- `unit` — optional unit suffix.
- `title` — optional label override.

The engine forwards this to the UI socket; the selection ring shows it.

## Conventions

- Update `_current_value` so `get_status()`/`get_display_info()` are consistent.
- Use `subprocess` with `capture_output=True` and a `timeout` — never let a
  plugin hang the daemon.
- Prefer the executor/uinput path first, then D-Bus, then CLI — in that order.
- Catch `FileNotFoundError`/`SubprocessError` and degrade gracefully.
- Follow plugin naming: directory = `name`, one class per plugin.

## Testing your plugin

```bash
~/.local/share/creatordial/.venv/bin/python3 - <<'EOF'
import sys
sys.path.insert(0, "/home/rootspectra/.local/share/creatordial")
from creatordial.plugins.mute import MutePlugin
p = MutePlugin()
print(p.execute("click"))   # simulate a center tap
EOF
```

The interactive `debug.py --input` mode lets you exercise gestures against a
hand-picked plugin too.