import os
import json
import logging
from typing import Optional

log = logging.getLogger("creatordial.config")

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/creatordial")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "enabled": False,
    "activation_time": 1.0,
    "rotation_threshold": 90.0,
    "sensitivity": 1.0,
    "inactivity_timeout": 0,
    "coactivator_key": "",
    "touchpad_disables_dialpad": True,
    "layout": {
        "circle_diameter": 1400,
        "center_button_diameter": 250,
        "circle_center_x": 770,
        "circle_center_y": 750,
        "top_right_icon_width": 250,
        "top_right_icon_height": 250,
    },
    "plugins": {
        "volume": {"enabled": True, "step": 5},
        "brightness": {"enabled": True, "step": 5},
        "gpu": {"enabled": True},
        "media": {"enabled": True},
        "keyboard": {"enabled": True},
        "screen": {"enabled": True},
        "nightlight": {"enabled": True},
    },
    "profiles": {},
    "theme": "default",
    "debug": False,
}


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self._config: dict = {}
        self._loaded = False

    def ensure_dir(self):
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

    def load(self) -> dict:
        self.ensure_dir()

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    self._config = json.load(f)
                self._loaded = True
                log.info("Config loaded from %s", self.config_path)
            except (json.JSONDecodeError, IOError) as e:
                log.warning("Failed to load config: %s, using defaults", e)
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()

        return self._config

    def save(self):
        self.ensure_dir()
        try:
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
            log.info("Config saved to %s", self.config_path)
        except IOError as e:
            log.error("Failed to save config: %s", e)

    def get(self, key: str, default=None):
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value):
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()

    @property
    def data(self) -> dict:
        return self._config

    def get_plugin_config(self, plugin_name: str) -> dict:
        return self._config.get("plugins", {}).get(plugin_name, {})

    def get_layout_config(self) -> dict:
        return self._config.get("layout", DEFAULT_CONFIG["layout"])

    def get_theme_name(self) -> str:
        return self._config.get("theme", "default")
