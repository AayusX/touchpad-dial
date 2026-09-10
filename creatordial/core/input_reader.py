import os
import math
import logging
import threading
from time import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from libevdev import EV_ABS, EV_KEY, EV_REL, Device, InputEvent

from .hardware_detector import TouchpadInfo

log = logging.getLogger("creatordial.input")


class ActivationMethod(Enum):
    TOP_RIGHT_ICON = "top_right_icon"
    DOUBLE_TAP = "double_tap"
    GESTURE = "gesture"


@dataclass
class TouchState:
    finger_down: bool = False
    touch_x: Optional[int] = None
    touch_y: Optional[int] = None
    touch_start_time: float = 0.0
    within_activation_zone: bool = False
    icon_activated: bool = False
    angle_start: Optional[float] = None
    last_angle: Optional[float] = None
    angle_accumulator: float = 0.0
    last_trigger_angle: Optional[float] = None
    center_button_triggered: bool = False
    center_enter_time: float = 0.0
    center_hold_fired: bool = False
    tap_disabled: bool = False
    first_touch_outside: bool = False

    def reset(self):
        self.finger_down = False
        self.touch_x = None
        self.touch_y = None
        self.within_activation_zone = False
        self.icon_activated = False
        self.angle_start = None
        self.last_angle = None
        self.angle_accumulator = 0.0
        self.last_trigger_angle = None
        self.center_button_triggered = False
        self.center_enter_time = 0.0
        self.center_hold_fired = False
        self.first_touch_outside = False


class InputReader:
    def __init__(
        self,
        touchpad: TouchpadInfo,
        circle_diameter: int = 1400,
        center_button_diameter: int = 250,
        circle_center_x: int = 770,
        circle_center_y: int = 750,
        top_right_icon_width: int = 250,
        top_right_icon_height: int = 250,
    ):
        self.touchpad = touchpad
        self.circle_diameter = circle_diameter
        self.center_button_diameter = center_button_diameter
        self.circle_center_x = circle_center_x
        self.circle_center_y = circle_center_y
        self.top_right_icon_width = top_right_icon_width
        self.top_right_icon_height = top_right_icon_height

        self.circle_radius = circle_diameter / 2
        self.center_button_radius = center_button_diameter / 2

        self.state = TouchState()
        self._fd = None
        self._device = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._on_rotation: Optional[Callable] = None
        self._on_click: Optional[Callable] = None
        self._on_double_click: Optional[Callable] = None
        self._on_long_press: Optional[Callable] = None
        self._on_activation: Optional[Callable] = None
        self._on_deactivation: Optional[Callable] = None
        self._on_center_release: Optional[Callable] = None

        self.activation_time = 1.0
        self.threshold = 90.0
        self.last_event_time = 0.0

    def set_callbacks(
        self,
        on_rotation: Optional[Callable] = None,
        on_click: Optional[Callable] = None,
        on_double_click: Optional[Callable] = None,
        on_long_press: Optional[Callable] = None,
        on_activation: Optional[Callable] = None,
        on_deactivation: Optional[Callable] = None,
        on_center_release: Optional[Callable] = None,
    ):
        self._on_rotation = on_rotation
        self._on_click = on_click
        self._on_double_click = on_double_click
        self._on_long_press = on_long_press
        self._on_activation = on_activation
        self._on_deactivation = on_deactivation
        self._on_center_release = on_center_release

    def open(self) -> bool:
        dev_path = f"/dev/input/event{self.touchpad.event_id}"
        try:
            self._fd = open(dev_path, "rb")
            self._device = Device(self._fd)
            log.info("Opened touchpad device: %s", dev_path)
            return True
        except (FileNotFoundError, PermissionError) as e:
            log.error("Cannot open %s: %s", dev_path, e)
            return False

    def grab(self):
        if self._device:
            try:
                self._device.grab()
                log.info("Touchpad grabbed (cursor disabled)")
            except Exception as e:
                log.error("Grab failed: %s", e)

    def ungrab(self):
        if self._device:
            try:
                self._device.ungrab()
                log.info("Touchpad released (cursor enabled)")
            except Exception as e:
                log.error("Ungrab failed: %s", e)

    def close(self):
        self._running = False
        self.ungrab()
        if self._fd:
            self._fd.close()
            self._fd = None
        log.info("Touchpad device closed")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._event_loop, daemon=True, name="input-reader")
        self._thread.start()
        log.info("Input reader started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.close()

    def _event_loop(self):
        if not self._device:
            log.error("No device open")
            return

        try:
            for event in self._device.events():
                if not self._running:
                    break
                self.last_event_time = time()
                self._process_event(event)
        except Exception as e:
            log.exception("Error in event loop: %s", e)

    def _process_event(self, event):
        if event.matches(EV_KEY.BTN_TOOL_FINGER):
            if event.value == 1:
                self.state.finger_down = True
                self.state.touch_start_time = time()
                self.state.angle_start = None
                self.state.angle_accumulator = 0.0
                log.debug("Finger down")
            elif event.value == 0:
                self._handle_finger_up()
                self.state.reset()
                log.debug("Finger up")
            return

        if event.matches(EV_ABS.ABS_MT_POSITION_X):
            self.state.touch_x = event.value
        elif event.matches(EV_ABS.ABS_MT_POSITION_Y):
            self.state.touch_y = event.value

        if self.state.touch_x is not None and self.state.touch_y is not None and self.state.finger_down:
            self._check_activation_zone()
            self._check_circle_area()

    def _check_activation_zone(self):
        tx, ty = self.state.touch_x, self.state.touch_y
        x_min = self.touchpad.max_x - self.top_right_icon_width
        x_max = self.touchpad.max_x
        y_min = 0
        y_max = self.top_right_icon_height

        in_zone = x_min <= tx <= x_max and y_min <= ty <= y_max

        if in_zone:
            if not self.state.within_activation_zone:
                self.state.within_activation_zone = True

            if (self.state.touch_start_time and
                not self.state.icon_activated and
                time() - self.state.touch_start_time >= self.activation_time):
                if self._on_activation:
                    self._on_activation()
                self.state.icon_activated = True
        else:
            if self.state.within_activation_zone:
                self.state.within_activation_zone = False
                self.state.touch_start_time = None
                self.state.icon_activated = False

    def _check_circle_area(self):
        tx, ty = self.state.touch_x, self.state.touch_y
        dx = tx - self.circle_center_x
        dy = ty - self.circle_center_y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        angle = (math.atan2(dy, dx) * 180 / math.pi + 90) % 360

        if self.state.angle_start is None:
            self.state.angle_start = angle

        if distance <= self.circle_radius:
            self.state.first_touch_outside = True

            if distance < self.center_button_radius:
                if not self.state.center_button_triggered:
                    self.state.center_button_triggered = True
                    self.state.center_enter_time = time()
                    self.state.center_hold_fired = False
                elapsed = time() - self.state.center_enter_time
                if elapsed >= self.activation_time and not self.state.center_hold_fired:
                    if self._on_long_press:
                        self._on_long_press()
                    self.state.center_hold_fired = True
            else:
                if self.state.center_button_triggered:
                    self.state.center_button_triggered = False
                    self.state.center_hold_fired = False

                self._process_rotation(angle)

    def _process_rotation(self, angle: float):
        if self.state.last_angle is None:
            self.state.last_angle = angle
            self.state.last_trigger_angle = angle
            self.state.angle_accumulator = 0.0
            return

        delta = angle - self.state.last_angle
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360

        self.state.angle_accumulator += delta
        self.state.last_angle = angle

        if abs(self.state.angle_accumulator) >= self.threshold:
            direction = "clockwise" if self.state.angle_accumulator > 0 else "counterclockwise"

            if self._on_rotation:
                self._on_rotation(direction, abs(self.state.angle_accumulator))

            self.state.angle_accumulator = 0.0

    def _handle_finger_up(self):
        if self.state.center_button_triggered:
            duration = time() - self.state.center_enter_time if self.state.center_enter_time else 0

            if duration < 0.3:
                if self._on_click:
                    self._on_click()

            if self._on_center_release:
                self._on_center_release()

            self.state.center_button_triggered = False
            self.state.center_hold_fired = False

        if not self.state.first_touch_outside and self.state.within_activation_zone:
            pass

    def update_dimensions(
        self,
        circle_diameter: Optional[int] = None,
        center_button_diameter: Optional[int] = None,
        circle_center_x: Optional[int] = None,
        circle_center_y: Optional[int] = None,
        top_right_icon_width: Optional[int] = None,
        top_right_icon_height: Optional[int] = None,
    ):
        if circle_diameter is not None:
            self.circle_diameter = circle_diameter
            self.circle_radius = circle_diameter / 2
        if center_button_diameter is not None:
            self.center_button_diameter = center_button_diameter
            self.center_button_radius = center_button_diameter / 2
        if circle_center_x is not None:
            self.circle_center_x = circle_center_x
        if circle_center_y is not None:
            self.circle_center_y = circle_center_y
        if top_right_icon_width is not None:
            self.top_right_icon_width = top_right_icon_width
        if top_right_icon_height is not None:
            self.top_right_icon_height = top_right_icon_height
