import os
import json
import logging
from typing import Optional

log = logging.getLogger("creatordial.themes")

THEMES_DIR = os.path.expanduser("~/.config/creatordial/themes")
SYSTEM_THEMES_DIR = "/usr/share/creatordial/themes"


DEFAULT_THEME = {
    "name": "default",
    "displayName": "Creator",
    "colors": {
        "background": "#0e131b",
        "centerBackground": "#1e2232",
        "ringColor": "#a5988a",
        "textPrimary": "#b9bab9",
        "textSecondary": "#787d82",
        "accent": "#a5988a",
        "border": "#282d3c",
        "activeSegment": "#a5988a",
    },
    "dimensions": {
        "boxWidth": 300,
        "boxHeight": 300,
    },
    "animation": {
        "fadeSpeed": 0.15,
        "transitionDuration": 200,
    },
    "font": {
        "family": "Inter",
        "weight": "DemiBold",
    },
}


PROART_THEME = {
    "name": "proart",
    "displayName": "ProArt",
    "colors": {
        "background": "#1a1a2e",
        "centerBackground": "#16213e",
        "ringColor": "#e94560",
        "textPrimary": "#f5f5f5",
        "textSecondary": "#a0a0a0",
        "accent": "#e94560",
        "border": "#0f3460",
        "activeSegment": "#e94560",
    },
    "dimensions": {
        "boxWidth": 320,
        "boxHeight": 320,
    },
    "animation": {
        "fadeSpeed": 0.12,
        "transitionDuration": 150,
    },
    "font": {
        "family": "Inter",
        "weight": "Bold",
    },
}

MINIMAL_THEME = {
    "name": "minimal",
    "displayName": "Minimal",
    "colors": {
        "background": "#ffffff",
        "centerBackground": "#f8f9fa",
        "ringColor": "#212529",
        "textPrimary": "#212529",
        "textSecondary": "#6c757d",
        "accent": "#0d6efd",
        "border": "#dee2e6",
        "activeSegment": "#0d6efd",
    },
    "dimensions": {
        "boxWidth": 280,
        "boxHeight": 280,
    },
    "animation": {
        "fadeSpeed": 0.2,
        "transitionDuration": 250,
    },
    "font": {
        "family": "Inter",
        "weight": "Regular",
    },
}


BUILTIN_THEMES = {
    "default": DEFAULT_THEME,
    "proart": PROART_THEME,
    "minimal": MINIMAL_THEME,
}


class ThemeManager:
    def __init__(self):
        self._themes: dict = {}
        self._current_theme: str = "default"
        self._load_themes()

    def _load_themes(self):
        self._themes = BUILTIN_THEMES.copy()

        for directory in [SYSTEM_THEMES_DIR, THEMES_DIR]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".json"):
                        filepath = os.path.join(directory, filename)
                        try:
                            with open(filepath) as f:
                                theme = json.load(f)
                            if "name" in theme:
                                self._themes[theme["name"]] = theme
                        except (json.JSONDecodeError, IOError):
                            pass

    def get_theme(self, name: Optional[str] = None) -> dict:
        return self._themes.get(name or self._current_theme, DEFAULT_THEME)

    def set_theme(self, name: str):
        if name in self._themes:
            self._current_theme = name

    def get_all_themes(self) -> dict:
        return self._themes

    def get_color(self, key: str) -> str:
        theme = self.get_theme()
        return theme.get("colors", {}).get(key, "#ffffff")

    def create_theme(self, theme: dict):
        if "name" in theme:
            self._themes[theme["name"]] = theme
            self._save_theme(theme)

    def _save_theme(self, theme: dict):
        os.makedirs(THEMES_DIR, exist_ok=True)
        filepath = os.path.join(THEMES_DIR, f"{theme['name']}.json")
        try:
            with open(filepath, "w") as f:
                json.dump(theme, f, indent=2)
        except IOError as e:
            log.error("Failed to save theme: %s", e)

    def delete_theme(self, name: str):
        if name in self._themes and name not in BUILTIN_THEMES:
            del self._themes[name]
            filepath = os.path.join(THEMES_DIR, f"{name}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
