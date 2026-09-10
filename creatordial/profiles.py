import os
import json
import logging
from typing import Optional

log = logging.getLogger("creatordial.profiles")

PROFILES_DIR = os.path.expanduser("~/.config/creatordial/profiles")
SYSTEM_PROFILES_DIR = "/usr/share/creatordial/profiles"


DEFAULT_PROFILES = {
    "default": {
        "id": "default",
        "displayName": "Default",
        "matchProcess": [],
        "matchTitle": [],
        "plugins": {
            "volume": {"enabled": True, "step": 5},
            "brightness": {"enabled": True, "step": 5},
        },
        "defaultPlugin": "volume",
    },
    "blender": {
        "id": "blender",
        "displayName": "Blender",
        "matchProcess": ["blender"],
        "matchTitle": ["Blender"],
        "plugins": {
            "volume": {"enabled": True, "step": 5},
            "scroll": {
                "enabled": True,
                "clockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTCTRL", "KEY_Y"]},
                "counterclockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTCTRL", "KEY_Z"]},
            },
        },
        "defaultPlugin": "volume",
    },
    "davinci-resolve": {
        "id": "davinci-resolve",
        "displayName": "DaVinci Resolve",
        "matchProcess": ["resolve"],
        "matchTitle": ["DaVinci Resolve"],
        "plugins": {
            "volume": {"enabled": True, "step": 5},
            "scroll": {"enabled": True},
        },
        "defaultPlugin": "volume",
    },
    "krita": {
        "id": "krita",
        "displayName": "Krita",
        "matchProcess": ["krita"],
        "matchTitle": ["Krita"],
        "plugins": {
            "brush_size": {
                "enabled": True,
                "clockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTBRACE"]},
                "counterclockwise_action": {"type": "key_combo", "keys": ["KEY_RIGHTBRACE"]},
            },
            "scroll": {"enabled": True},
        },
        "defaultPlugin": "scroll",
    },
    "vscode": {
        "id": "vscode",
        "displayName": "VS Code",
        "matchProcess": ["code", "code-oss", "code-insiders"],
        "matchTitle": ["Visual Studio Code", "VS Code"],
        "plugins": {
            "zoom": {
                "enabled": True,
                "clockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTCTRL", "KEY_EQUAL"]},
                "counterclockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTCTRL", "KEY_MINUS"]},
            },
            "scroll": {"enabled": True},
        },
        "defaultPlugin": "scroll",
    },
    "browser": {
        "id": "browser",
        "displayName": "Browser",
        "matchProcess": ["firefox", "chrome", "chromium", "brave"],
        "matchTitle": ["Firefox", "Chrome", "Chromium", "Brave"],
        "plugins": {
            "scroll": {"enabled": True},
            "zoom": {
                "enabled": True,
                "clockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTCTRL", "KEY_EQUAL"]},
                "counterclockwise_action": {"type": "key_combo", "keys": ["KEY_LEFTCTRL", "KEY_MINUS"]},
            },
        },
        "defaultPlugin": "scroll",
    },
}


class ProfileManager:
    def __init__(self):
        self._profiles: dict = {}
        self._current_profile: str = "default"
        self._auto_detect = True

    def load_profiles(self):
        self._profiles = DEFAULT_PROFILES.copy()

        for directory in [SYSTEM_PROFILES_DIR, PROFILES_DIR]:
            if os.path.exists(directory):
                self._load_from_dir(directory)

        log.info("Loaded %d profiles", len(self._profiles))

    def _load_from_dir(self, directory: str):
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath) as f:
                        profile = json.load(f)
                    if "id" in profile:
                        self._profiles[profile["id"]] = profile
                        log.debug("Loaded profile: %s", profile["id"])
                except (json.JSONDecodeError, IOError) as e:
                    log.warning("Failed to load profile %s: %s", filepath, e)

    def get_profile(self, name: str) -> Optional[dict]:
        return self._profiles.get(name)

    def get_all_profiles(self) -> dict:
        return self._profiles

    def set_current_profile(self, name: str):
        if name in self._profiles:
            self._current_profile = name

    def match_profile(self, binary: Optional[str], title: Optional[str]) -> str:
        if not self._auto_detect:
            return self._current_profile

        if binary:
            binary_lower = binary.lower()
            for name, profile in self._profiles.items():
                for proc in profile.get("matchProcess", []):
                    if proc.lower() in binary_lower:
                        return name

        if title:
            title_lower = title.lower()
            for name, profile in self._profiles.items():
                for t in profile.get("matchTitle", []):
                    if t.lower() in title_lower:
                        return name

        return "default"

    def create_profile(self, profile: dict):
        if "id" in profile:
            self._profiles[profile["id"]] = profile
            self._save_profile(profile)

    def _save_profile(self, profile: dict):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        filepath = os.path.join(PROFILES_DIR, f"{profile['id']}.json")
        try:
            with open(filepath, "w") as f:
                json.dump(profile, f, indent=2)
        except IOError as e:
            log.error("Failed to save profile: %s", e)

    def delete_profile(self, name: str):
        if name in self._profiles and name != "default":
            del self._profiles[name]
            filepath = os.path.join(PROFILES_DIR, f"{name}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
