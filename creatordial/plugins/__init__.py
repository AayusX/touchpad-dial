import logging
from abc import ABC, abstractmethod
from typing import Optional

log = logging.getLogger("creatordial.plugin")


class BasePlugin(ABC):
    def __init__(self):
        self.name: str = ""
        self.icon: str = ""
        self.display_name: str = ""
        self._config: dict = {}
        self._current_value = 0
        self._executor = None

    @abstractmethod
    def execute(self, direction: str, magnitude: float = 0) -> Optional[dict]:
        pass

    def set_executor(self, executor):
        self._executor = executor

    def configure(self, config: dict):
        self._config = config

    def get_display_info(self) -> dict:
        return {
            "value": self._current_value,
            "title": self.display_name,
        }

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "value": self._current_value,
        }
