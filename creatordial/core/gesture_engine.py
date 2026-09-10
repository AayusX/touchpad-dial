import logging
import math
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

log = logging.getLogger("creatordial.gesture")


class GestureType(Enum):
    ROTATION_CW = "rotation_cw"
    ROTATION_CCW = "rotation_ccw"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    LONG_PRESS = "long_press"
    SWIPE = "swipe"


@dataclass
class GestureEvent:
    gesture_type: GestureType
    direction: Optional[str] = None
    magnitude: float = 0.0
    duration: float = 0.0


@dataclass
class GestureConfig:
    activation_distance: int = 200
    activation_speed: float = 100.0
    activation_time: float = 1.0
    sensitivity: float = 1.0
    rotation_threshold: float = 90.0
    double_click_interval: float = 0.3
    long_press_duration: float = 1.0
    debounce_time: float = 0.05


class GestureEngine:
    def __init__(self, config: Optional[GestureConfig] = None):
        self.config = config or GestureConfig()
        self._callbacks: dict[GestureType, list[Callable]] = {}
        self._rotation_accumulator = 0.0
        self._last_rotation_angle: Optional[float] = None
        self._last_click_time = 0.0
        self._click_count = 0

        for gt in GestureType:
            self._callbacks[gt] = []

    def register_callback(self, gesture_type: GestureType, callback: Callable):
        self._callbacks[gesture_type].append(callback)

    def unregister_callback(self, gesture_type: GestureType, callback: Callable):
        if callback in self._callbacks[gesture_type]:
            self._callbacks[gesture_type].remove(callback)

    def emit(self, event: GestureEvent):
        for cb in self._callbacks.get(event.gesture_type, []):
            try:
                cb(event)
            except Exception as e:
                log.error("Gesture callback error: %s", e)

    def process_rotation(self, angle: float):
        if self._last_rotation_angle is None:
            self._last_rotation_angle = angle
            return

        delta = angle - self._last_rotation_angle
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360

        delta *= self.config.sensitivity
        self._rotation_accumulator += delta
        self._last_rotation_angle = angle

        if abs(self._rotation_accumulator) >= self.config.rotation_threshold:
            direction = GestureType.ROTATION_CW if self._rotation_accumulator > 0 else GestureType.ROTATION_CCW
            event = GestureEvent(
                gesture_type=direction,
                direction="clockwise" if self._rotation_accumulator > 0 else "counterclockwise",
                magnitude=abs(self._rotation_accumulator),
            )
            self._emit(event)
            self._rotation_accumulator = 0.0

    def process_click(self, duration: float):
        from time import time as _time
        now = _time()

        if now - self._last_click_time < self.config.double_click_interval:
            self._click_count += 1
            if self._click_count >= 2:
                event = GestureEvent(gesture_type=GestureType.DOUBLE_CLICK)
                self._emit(event)
                self._click_count = 0
        else:
            self._click_count = 1

            if duration >= self.config.long_press_duration:
                event = GestureEvent(
                    gesture_type=GestureType.LONG_PRESS,
                    duration=duration,
                )
                self._emit(event)
            else:
                event = GestureEvent(gesture_type=GestureType.CLICK, duration=duration)
                self._emit(event)

        self._last_click_time = now

    def reset_rotation(self):
        self._rotation_accumulator = 0.0
        self._last_rotation_angle = None

    def reset_all(self):
        self.reset_rotation()
        self._click_count = 0
        self._last_click_time = 0.0
