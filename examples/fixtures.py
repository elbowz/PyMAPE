from __future__ import annotations

# import numpy
import random
import logging
import asyncio

from typing import Callable, Any

logger = logging.getLogger(__name__)


class VirtualCar:
    def __init__(self,
                 uid='Car',
                 speed: int = 50,
                 speed_limit: int | None = None,
                 hazard_lights: bool = False,
                 emergency_detect: bool = False
                 ) -> None:
        logger.info(f"Init {self.__class__.__name__} {uid}...")

        self.uid: str = uid
        self.speed: int = speed
        self.speed_limit: int = speed_limit or speed + 20
        self.hazard_lights: bool = hazard_lights
        self.emergency_detect: bool = emergency_detect
        self._callbacks: dict = {}

        self._task_service_loop = asyncio.create_task(self._service_loop())

    async def _service_loop(self):
        while True and not self._task_service_loop.cancelled():
            # if numpy.random.choice((True, False), p=[0.1, 0.9]):
            #     self.hazard_lights = True

            delta_speed = max(random.randint(0, 3), int(abs(self.speed_limit - self._speed) / 4))

            if self._speed >= self.speed_limit:
                self._speed -= delta_speed
            else:
                self._speed += delta_speed

            self.speed = max(0, self.speed)

            await asyncio.sleep(random.uniform(2, 4))

    def __del__(self):
        self._task_service_loop.cancel()

    def set_callback(self, name: str, callback: Callable, init=True):
        if name not in self._callbacks:
            self._callbacks[name] = [callback]
        else:
            self._callbacks[name].append(callback)

        if init and (value := getattr(self, name, None)) is not None:
            callback({name: value})

    def __setattr__(self, name: str, value: Any) -> None:
        old_value = getattr(self, name, None)

        super().__setattr__(name, value)

        if hasattr(self, '_callbacks') and (callbacks := self._callbacks.get(name, None)):
            for callback in callbacks:
                callback({name: value})

    @property
    def emergency_detect(self):
        return self._emergency_detect

    @emergency_detect.setter
    def emergency_detect(self, state: bool):
        logger.info(f"{self.__class__.__name__} {self.uid} emergency {'ON' if state else 'OFF'}")
        self._emergency_detect = state

    @property
    def hazard_lights(self):
        return self._hazard_lights

    @hazard_lights.setter
    def hazard_lights(self, state: bool):
        logger.info(f"{self.__class__.__name__} {self.uid} hazard lights {'ON' if state else 'OFF'}")
        self._hazard_lights = state

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed: int):
        logger.info(f"{self.__class__.__name__} {self.uid} speed: {speed} Km/h")
        self._speed = speed

    @property
    def speed_limit(self):
        return self._speed_limit

    @speed_limit.setter
    def speed_limit(self, speed: int):
        logger.info(f"{self.__class__.__name__} {self.uid} speed limit set: {speed} Km/h")
        self._speed_limit = speed


class VirtualAmbulance(VirtualCar):
    def __init__(self, uid='', speed: int = 50, speed_limit: int | None = None, hazard_lights: bool = False,
                 emergency_detect: bool = False, siren: bool = False) -> None:
        super().__init__(uid, speed, speed_limit, hazard_lights, emergency_detect)
        self.siren = siren

    @property
    def siren(self):
        return self._siren

    @siren.setter
    def siren(self, state: bool):
        logger.info(f"{self.__class__.__name__} {self.uid} siren: {'ON' if state else 'OFF'}")
        self._siren = state
