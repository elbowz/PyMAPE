from __future__ import annotations

import random
import logging
import asyncio

import numpy

from typing import Callable, Any
from mape.utils import log_task_exception

logger = logging.getLogger(__name__)


class VirtualRoom:
    def __init__(self, init_temperature: float = 20, init_air_quality: float = 40, uid='Generic') -> None:
        self.uid = uid
        self.heater_state = False
        self.fan_speed = 0
        self._current_temperature = init_temperature
        self._current_air_quality = init_air_quality

    def tick_temperature(self):

        tick_value = random.uniform(0, 1)

        if self.heater_state:
            self._current_temperature += tick_value
        else:
            self._current_temperature -= tick_value

    def tick_air_quality(self):
        tick_value = random.uniform(0, 6)
        self._current_air_quality = self._current_air_quality + self.fan_speed - tick_value

    def set_heater(self, state: bool):
        logger.info(f"Heater {self.uid} set to {'ON' if state else 'OFF'}")
        self.heater_state = state

    def set_fan(self, speed: int):
        logger.info(f"Fan {self.uid} set to speed: {speed}")
        self.fan_speed = speed

    @property
    def current_temperature(self):
        self.tick_temperature()
        return self._current_temperature

    @property
    def current_air_quality(self):
        self.tick_air_quality()
        return self._current_air_quality
