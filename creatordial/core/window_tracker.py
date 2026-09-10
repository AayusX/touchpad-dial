import subprocess
import json
import os
import logging
from typing import Optional

log = logging.getLogger("creatordial.window")


class WindowTracker:
    def __init__(self):
        self._session_type = os.environ.get("XDG_SESSION_TYPE", "")
        self._compositor = self._detect_compositor()
        self._current_app: Optional[str] = None
        self._current_title: Optional[str] = None

    @staticmethod
    def _detect_compositor() -> str:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop:
            return "gnome"
        elif "kde" in desktop:
            return "kde"
        elif "sway" in desktop:
            return "sway"
        elif "hyprland" in desktop:
            return "hyprland"
        return "unknown"

    def get_active_window(self) -> tuple[Optional[str], Optional[str]]:
        binary = None
        title = None

        if self._session_type == "x11":
            binary, title = self._get_x11()
        else:
            for method in [self._get_kde_wayland, self._get_gnome_wayland,
                          self._get_sway, self._get_hyprland]:
                binary, title = method()
                if binary or title:
                    break

        self._current_app = binary
        self._current_title = title
        return binary, title

    def _get_x11(self) -> tuple[Optional[str], Optional[str]]:
        try:
            root_cmd = ["xdotool", "getactivewindow"]
            win_id = subprocess.check_output(root_cmd, stderr=subprocess.DEVNULL).decode().strip()

            title_cmd = ["xdotool", "getwindowname", win_id]
            title = subprocess.check_output(title_cmd, stderr=subprocess.DEVNULL).decode().strip()

            pid_cmd = ["xdotool", "getwindowpid", win_id]
            pid = subprocess.check_output(pid_cmd, stderr=subprocess.DEVNULL).decode().strip()
            binary = self._binary_from_pid(pid)

            return binary, title
        except (subprocess.SubprocessError, FileNotFoundError):
            return None, None

    def _get_kde_wayland(self) -> tuple[Optional[str], Optional[str]]:
        qdbus = None
        for name in ["qdbus", "qdbus6", "qdbus-qt6"]:
            path = subprocess.run(["which", name], capture_output=True, text=True).stdout.strip()
            if path:
                qdbus = name
                break
        if not qdbus:
            return None, None

        try:
            win_id = subprocess.check_output(
                [qdbus, "org.kde.KWin", "/KWin", "org.kde.KWin.activeWindow"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            title = subprocess.check_output(
                [qdbus, "org.kde.KWin", f"/org/kde/KWin/Window/{win_id}",
                 "org.kde.KWin.Window.caption"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            pid = subprocess.check_output(
                [qdbus, "org.kde.KWin", f"/org/kde/KWin/Window/{win_id}",
                 "org.kde.KWin.Window.pid"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            binary = self._binary_from_pid(pid)
            return binary, title
        except (subprocess.SubprocessError, FileNotFoundError):
            return None, None

    def _get_gnome_wayland(self) -> tuple[Optional[str], Optional[str]]:
        try:
            result = subprocess.check_output(
                ["gdbus", "call", "--session",
                 "--dest", "org.gnome.Shell",
                 "--object-path", "/org/gnome/Shell",
                 "--method", "org.gnome.Shell.Eval",
                 "global.get_window_actors().find(w => w.meta_window.has_focus())?.meta_window.get_title()"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            title = result.strip("'\"") if result else None
            return None, title
        except (subprocess.SubprocessError, FileNotFoundError):
            return None, None

    def _get_sway(self) -> tuple[Optional[str], Optional[str]]:
        try:
            out = subprocess.check_output(
                ["swaymsg", "-t", "get_tree"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            tree = json.loads(out)
            focused = self._find_sway_focused(tree)
            if focused:
                title = focused.get("name")
                pid = focused.get("pid")
                binary = self._binary_from_pid(pid) if pid else None
                return binary, title
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            pass
        return None, None

    @staticmethod
    def _find_sway_focused(node: dict) -> Optional[dict]:
        if node.get("focused"):
            return node
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            result = WindowTracker._find_sway_focused(child)
            if result:
                return result
        return None

    def _get_hyprland(self) -> tuple[Optional[str], Optional[str]]:
        try:
            out = subprocess.check_output(
                ["hyprctl", "activewindow", "-j"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            win = json.loads(out)
            title = win.get("title")
            pid = win.get("pid")
            binary = self._binary_from_pid(pid) if pid else None
            return binary, title
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            return None, None

    @staticmethod
    def _binary_from_pid(pid) -> Optional[str]:
        try:
            return os.readlink(f"/proc/{pid}/exe")
        except (FileNotFoundError, PermissionError, TypeError):
            return None

    def match_profile(self, profiles: dict, binary: Optional[str], title: Optional[str]) -> str:
        if binary:
            binary_lower = binary.lower()
            for app_name in profiles:
                if app_name in binary_lower:
                    return app_name

        if title:
            title_lower = title.lower()
            for app_name in profiles:
                if app_name in title_lower:
                    return app_name

        return "default"
