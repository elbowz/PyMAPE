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


class VirtualCar:
    def __init__(self,
                 uid='Car',
                 speed: int = 50,
                 speed_limit: int | None = None,
                 hazard_lights: bool = False,
                 emergency_detect: bool = False
                 ) -> None:
        self.uid: str = uid
        self.speed: int = speed
        self.speed_limit: int = speed_limit or speed + 20
        self.hazard_lights: bool = hazard_lights
        self.emergency_detect: bool = emergency_detect
        self._callbacks: dict = {}

        logger.info(f"Init car {uid}...")

        self._task_service_loop = asyncio.create_task(self._service_loop())

    async def _service_loop(self):
        while True and not self._task_service_loop.cancelled():
            # if numpy.random.choice((True, False), p=[0.1, 0.9]):
            #     self.hazard_lights = True

            delta_speed = max(random.randint(0, 3), int(abs(self.speed_limit - self.speed) / 4))

            if self.speed >= self.speed_limit:
                self.speed -= delta_speed
            else:
                self.speed += delta_speed

            await asyncio.sleep(random.uniform(2, 4))

    def __del__(self):
        self._task_service_loop.cancel()

    def set_callback(self, name: str, callback: Callable, init=True):
        self._callbacks[name] = callback

        if init and (value := getattr(self, name, None)):
            callback({name: value})

    def __setattr__(self, name: str, value: Any) -> None:
        old_value = getattr(self, name, None)

        super().__setattr__(name, value)

        if hasattr(self, '_callbacks') and (callback := self._callbacks.get(name, None)):
            callback({name: value})

    @property
    def emergency_detect(self):
        return self._emergency_detect

    @emergency_detect.setter
    def emergency_detect(self, state: bool):
        logger.info(f"Car {self.uid} emergency {'ON' if state else 'OFF'}")
        self._emergency_detect = state

    @property
    def hazard_lights(self):
        return self._hazard_lights

    @hazard_lights.setter
    def hazard_lights(self, state: bool):
        logger.info(f"Car {self.uid} hazard lights {'ON' if state else 'OFF'}")
        self._hazard_lights = state

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed: int):
        logger.info(f"Car {self.uid} speed: {speed} Km/h")
        self._speed = speed

    @property
    def speed_limit(self):
        return self._speed_limit

    @speed_limit.setter
    def speed_limit(self, speed: int):
        logger.info(f"Car {self.uid} speed limit set: {speed} Km/h")
        self._speed_limit = speed
