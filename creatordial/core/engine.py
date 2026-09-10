import logging
import threading
import time
from typing import Optional

from .hardware_detector import HardwareDetector, HardwareProfile
from .i2c_controller import I2CController
from .input_reader import InputReader
from .gesture_engine import GestureEngine, GestureType, GestureEvent
from .action_executor import ActionExecutor
from .window_tracker import WindowTracker
from .ui_ipc import UIIPCServer

log = logging.getLogger("creatordial.engine")


class DialEngine:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or self._default_config()
        self._hardware: Optional[HardwareProfile] = None
        self._i2c: Optional[I2CController] = None
        self._input: Optional[InputReader] = None
        self._gesture = GestureEngine()
        self._executor = ActionExecutor()
        self._window_tracker = WindowTracker()
        self._ui_ipc = UIIPCServer()

        self._active = False
        self._current_plugin = "volume"
        self._current_profile = "default"
        self._profiles: dict = {}
        self._plugins: dict = {}
        self._inactivity_timer: Optional[threading.Timer] = None
        self._last_click_time = 0.0
        self._selection_mode = False
        self._selection_index = 0

        self._setup_gesture_callbacks()

    @staticmethod
    def _default_config() -> dict:
        return {
            "enabled": False,
            "activation_time": 1.0,
            "rotation_threshold": 90.0,
            "sensitivity": 1.0,
            "inactivity_timeout": 0,
            "top_right_icon_width": 250,
            "top_right_icon_height": 250,
            "circle_diameter": 1400,
            "center_button_diameter": 250,
            "circle_center_x": 770,
            "circle_center_y": 750,
        }

    def _setup_gesture_callbacks(self):
        self._gesture.register_callback(GestureType.ROTATION_CW, self._on_rotation_cw)
        self._gesture.register_callback(GestureType.ROTATION_CCW, self._on_rotation_ccw)
        self._gesture.register_callback(GestureType.CLICK, self._on_click)
        self._gesture.register_callback(GestureType.DOUBLE_CLICK, self._on_double_click)
        self._gesture.register_callback(GestureType.LONG_PRESS, self._on_long_press)

    def detect_hardware(self) -> HardwareProfile:
        detector = HardwareDetector()
        self._hardware = detector.detect()

        if self._hardware.touchpad:
            self._i2c = I2CController(
                bus=self._hardware.i2c_bus,
                addr=self._hardware.i2c_addr,
            )

        return self._hardware

    def load_profiles(self, profiles: dict):
        self._profiles = profiles
        log.info("Loaded %d profiles", len(profiles))

    def register_plugin(self, name: str, plugin):
        self._plugins[name] = plugin
        if hasattr(plugin, "set_executor"):
            plugin.set_executor(self._executor)
        log.info("Registered plugin: %s", name)

    def get_plugin(self, name: str):
        return self._plugins.get(name)

    def start(self) -> bool:
        if not self._hardware or not self._hardware.touchpad:
            log.error("Hardware not detected. Call detect_hardware() first.")
            return False

        self._executor.initialize_virtual_device("Creator Dial")
        self._ui_ipc.start()

        layout = self.config.get("layout", {})

        self._input = InputReader(
            touchpad=self._hardware.touchpad,
            circle_diameter=layout.get("circle_diameter", 1400),
            center_button_diameter=layout.get("center_button_diameter", 250),
            circle_center_x=layout.get("circle_center_x", 770),
            circle_center_y=layout.get("circle_center_y", 750),
            top_right_icon_width=layout.get("top_right_icon_width", 250),
            top_right_icon_height=layout.get("top_right_icon_height", 250),
        )

        self._input.activation_time = self.config.get("activation_time", 1.0)
        self._gesture.config.rotation_threshold = self.config.get("rotation_threshold", 90.0)
        self._gesture.config.sensitivity = self.config.get("sensitivity", 1.0)

        self._input.set_callbacks(
            on_activation=self._activate,
            on_deactivation=self._deactivate,
            on_rotation=self._gesture_rotation,
            on_click=self._gesture_click,
            on_double_click=self._gesture_double_click,
            on_long_press=self._on_center_hold,
            on_center_release=self._on_center_release,
        )

        if not self._input.open():
            log.error("Failed to open touchpad device")
            return False

        self._input.start()
        log.info("Dial engine started")
        return True

    def stop(self):
        if self._input:
            self._input.stop()
        if self._i2c and self._active:
            self._i2c.deactivate_dialpad()
        self._executor.cleanup()
        self._ui_ipc.stop()
        log.info("Dial engine stopped")

    def _activate(self):
        if self._active:
            self._deactivate()
            return

        if self._i2c:
            self._i2c.activate_dialpad()

        if self._input:
            self._input.grab()

        self._active = True
        log.info("DialPad activated")

    def _deactivate(self):
        if not self._active:
            return

        if self._i2c:
            self._i2c.deactivate_dialpad()

        if self._input:
            self._input.ungrab()

        self._active = False
        self._selection_mode = False
        self._gesture.reset_all()
        log.info("DialPad deactivated")

    def toggle(self):
        if self._active:
            self._deactivate()
        else:
            self._activate()

    def _gesture_rotation(self, direction: str, magnitude: float):
        gesture_type = (
            GestureType.ROTATION_CW if direction == "clockwise" else GestureType.ROTATION_CCW
        )
        self._gesture.emit(
            GestureEvent(
                gesture_type=gesture_type,
                direction=direction,
                magnitude=magnitude,
            )
        )

    def _gesture_click(self):
        from time import time as _time
        now = _time()
        delta = now - self._last_click_time
        self._last_click_time = now

        if delta < self._gesture.config.double_click_interval:
            self._gesture.emit(GestureEvent(gesture_type=GestureType.DOUBLE_CLICK))
            self._last_click_time = 0.0
        else:
            self._gesture.emit(GestureEvent(gesture_type=GestureType.CLICK))

    def _gesture_double_click(self):
        self._gesture.emit(GestureEvent(gesture_type=GestureType.DOUBLE_CLICK))

    def _on_center_hold(self):
        if not self._active:
            return
        if self._selection_mode:
            return
        self._selection_mode = True
        self._selection_index = 0
        plugin_names = list(self._plugins.keys())
        plugin_icons = [self._plugins[k].icon if hasattr(self._plugins[k], "icon") else "" for k in plugin_names]
        self._ui_ipc.send_selection(plugin_names, plugin_icons, plugin_names[self._selection_index])
        log.info("Selection mode entered: %s", plugin_names)

    def _on_center_release(self):
        if not self._selection_mode:
            return
        plugin_names = list(self._plugins.keys())
        if plugin_names:
            chosen = plugin_names[self._selection_index]
            if chosen != self._current_plugin:
                self._current_plugin = chosen
                self._update_plugin_display()
                log.info("Plugin selected: %s", chosen)
        self._selection_mode = False
        self._selection_index = 0
        self._ui_ipc.send_selection_done()
        log.info("Selection mode exited")

    def _on_rotation_cw(self, event: GestureEvent):
        if not self._active:
            return
        if self._selection_mode:
            plugin_names = list(self._plugins.keys())
            if plugin_names:
                self._selection_index = (self._selection_index + 1) % len(plugin_names)
                plugin_icons = [self._plugins[k].icon if hasattr(self._plugins[k], "icon") else "" for k in plugin_names]
                self._ui_ipc.send_selection(plugin_names, plugin_icons, plugin_names[self._selection_index])
            return
        self._execute_plugin_action("clockwise", event.magnitude)
        log.debug("Rotation CW: %.1f", event.magnitude)

    def _on_rotation_ccw(self, event: GestureEvent):
        if not self._active:
            return
        if self._selection_mode:
            plugin_names = list(self._plugins.keys())
            if plugin_names:
                self._selection_index = (self._selection_index - 1) % len(plugin_names)
                plugin_icons = [self._plugins[k].icon if hasattr(self._plugins[k], "icon") else "" for k in plugin_names]
                self._ui_ipc.send_selection(plugin_names, plugin_icons, plugin_names[self._selection_index])
            return
        self._execute_plugin_action("counterclockwise", event.magnitude)
        log.debug("Rotation CCW: %.1f", event.magnitude)

    def _on_click(self, event: GestureEvent):
        if not self._active:
            return
        self._cycle_plugins()
        log.debug("Click -> cycle plugin")

    def _on_double_click(self, event: GestureEvent):
        if not self._active:
            return
        self._cycle_plugins()
        log.debug("Double click -> cycle plugins")

    def _on_long_press(self, event: GestureEvent):
        if not self._active:
            return
        self._execute_plugin_action("long_press")
        log.debug("Long press")

    def _execute_plugin_action(self, direction: str, magnitude: float = 0):
        plugin = self._plugins.get(self._current_plugin)
        if plugin:
            try:
                value = plugin.execute(direction, magnitude)
                if value is not None:
                    self._ui_ipc.send_value(
                        value.get("value"),
                        unit=value.get("unit"),
                        title=value.get("title", self._current_plugin),
                    )
            except Exception as e:
                log.error("Plugin execution error: %s", e)

    def _update_plugin_display(self):
        plugin = self._plugins.get(self._current_plugin)
        if plugin and hasattr(plugin, "get_display_info"):
            info = plugin.get_display_info()
            self._ui_ipc.send_titles(
                list(self._plugins.keys()),
                [self._plugins[k].icon if hasattr(self._plugins[k], "icon") else "" for k in self._plugins],
                self._current_plugin,
            )
            if "value" in info:
                self._ui_ipc.send_value(info["value"], title=self._current_plugin)

    def _cycle_plugins(self):
        plugin_names = list(self._plugins.keys())
        if not plugin_names:
            return

        current_idx = plugin_names.index(self._current_plugin) if self._current_plugin in plugin_names else -1
        next_idx = (current_idx + 1) % len(plugin_names)
        self._current_plugin = plugin_names[next_idx]

        self._update_plugin_display()
        log.info("Switched to plugin: %s", self._current_plugin)

    def switch_plugin(self, name: str):
        if name in self._plugins:
            self._current_plugin = name
            self._update_plugin_display()

    def _reset_inactivity_timer(self):
        if self._inactivity_timer:
            self._inactivity_timer.cancel()

        timeout = self.config.get("inactivity_timeout", 0)
        if timeout > 0 and self._active:
            self._inactivity_timer = threading.Timer(timeout, self._deactivate)
            self._inactivity_timer.daemon = True
            self._inactivity_timer.start()

    def set_profile(self, profile_name: str):
        if profile_name in self._profiles:
            self._current_profile = profile_name
            profile = self._profiles[profile_name]
            for plugin_name, plugin_config in profile.get("plugins", {}).items():
                plugin = self._plugins.get(plugin_name)
                if plugin and hasattr(plugin, "configure"):
                    plugin.configure(plugin_config)
            self._update_plugin_display()
            log.info("Profile switched to: %s", profile_name)

    def auto_detect_profile(self):
        binary, title = self._window_tracker.get_active_window()
        matched = self._window_tracker.match_profile(self._profiles, binary, title)
        if matched != self._current_profile:
            self.set_profile(matched)
