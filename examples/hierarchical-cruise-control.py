#!/usr/bin/env python3
import asyncio
import logging
from typing import Any, Optional, Callable

from simple_pid import PID

import mape
from mape.utils import LogObserver, init_logger, task_exception, setdefaultattr
from mape.loop import Loop
from mape.base_elements import Plan, Element
from mape.typing import CallMethod
from mape import operators as ops
from mape.remote.influxdb import InfluxObserver

logger = init_logger()
logger.setLevel(logging.DEBUG)

mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


async def create_hold_distance(car, car_in_front):
    """ MAPE Loop and elements definition """
    loop = Loop(uid=f'hold_distance_{car.uid}')

    @loop.monitor
    def distance(item, on_next, self):
        gap = car_in_front.position - item['position']
        logger.debug(f"{car.uid} - {car_in_front.uid} = {gap} m")
        on_next(gap)

    @loop.plan()
    def pid(distance, on_next, self):
        # Calculate the speed, through pid controller
        speed = self.pid(distance)
        on_next(speed)

    # Init and configure the pid
    # Set coefficients for proportional, integral, and derivative terms, and target distance
    distance_target = 250
    pid.pid = PID(-5, -0.01, -0.1, setpoint=distance_target)
    # Limit the speed range returned from pid
    pid.pid.output_limits = (0, 160)

    @loop.execute
    def speed(speed, on_next):
        on_next(CallMethod.create('cruise_control', speed))

    # for element in loop:
    #     element.debug(Element.Debug.IN)

    """ MAPE Elements LOCAL connection """
    distance.subscribe(pid)
    pid.subscribe(speed)

    # Use InfluxDB sink/terminator to store distance from the car in front
    distance.subscribe(InfluxObserver(tags=('type', f"distance")))

    # Hierarchical connection
    speed.subscribe(mape.app[f"cruise_control_{car.uid}.pid"])

    # Starting monitor...
    logger.info(f"{distance} element started")
    distance.start()

    car.set_callback('position', distance, init=True)


async def create_cruise_control(car):
    """ MAPE Loop and elements definition """
    loop = Loop(uid=f'cruise_control_{car.uid}')

    @loop.monitor
    def speed(item, on_next, self):
        on_next(item['speed'])

    @loop.register(uid='pid')
    class Pid(Plan):
        def __init__(self, loop, speed_target=100, uid=None):
            self.speed_target = speed_target

            # Init and configure the pid
            # Set coefficients for proportional, integral, and derivative terms, and target speed
            self.pid = PID(4, 0.01, 0.1, setpoint=speed_target)
            # Limit the returned values from pid (ie. car Brake capabilities and Hp)
            self.pid.output_limits = (-car.max_break, car.max_power)

            super().__init__(loop, uid=uid)

        def cruise_control(self, speed_target):
            self.pid.setpoint = speed_target
            self.speed_target = speed_target

        def reactivity(self, proportional_k):
            self.pid.Kp = proportional_k

        def _on_next(self, current_speed, on_next=None, *args, **kwargs):
            # Calculate the acceleration or brake needed, through pid controller
            # https://en.wikipedia.org/wiki/PID_controller
            power = self.pid(current_speed)
            on_next(power)

    @loop.execute
    async def gas_brake(value, on_next):
        if value >= 0:
            await car.gas(value)          # Accelerate
        elif value < 0:
            await car.brake(value)        # Brake

    # for element in loop:
    #     element.debug(Element.Debug.IN | Element.Debug.OUT)

    """ MAPE Elements LOCAL connection """
    speed.subscribe(loop.pid)
    loop.pid.subscribe(gas_brake)

    # Use InfluxDB sink/terminator to store distance from the car in front
    speed.subscribe(InfluxObserver(tags=(('type', 'speed'), ('car', car.uid))))
    loop.pid.subscribe(InfluxObserver(tags=(('type', 'power'), ('car', car.uid))))

    # Starting monitor...
    logger.info(f"{speed} element started")
    speed.start()

    car.set_callback('speed', speed, init=True)


async def async_main():
    from fixtures import VirtualCarSpeed

    # Managed elements
    car = VirtualCarSpeed('Panda', speed=0, max_power=70, max_break=70, position=0)
    car_in_front = VirtualCarSpeed('Countach', speed=0, max_power=200, max_break=180, position=0)

    await create_cruise_control(car)
    await create_hold_distance(car, car_in_front)
    await create_cruise_control(car_in_front)

    # Stdin/key bindings setup for user input
    prompt_setup(mape.app['cruise_control_Countach.pid'])


def prompt_setup(planner):
    from utils import handle_prompt

    def prompt_handler(value):
        if value in ['exit', 'close', 'stop']:
            mape.stop()

    def key_enter_exit(key):
        if key == 'f1':
            planner.cruise_control(planner.speed_target+10)
        elif key == 'f2':
            planner.cruise_control(planner.speed_target-10)

    def key_close_handler(key):
        mape.stop()

    key_bindings_handlers = {'f1': key_enter_exit, 'f2': key_enter_exit, 'c-c': key_close_handler}
    asyncio.create_task(task_exception(handle_prompt(prompt_handler, key_bindings_handlers)))


if __name__ == '__main__':
    logger.debug('START...')

    # CLI EXAMPLES
    # * python -m hierarchical-cruise-control
    #
    # notes:
    #   * "python -m hierarchical-cruise-control" == "python hierarchical-cruise-control.py" == "./hierarchical-cruise-control.py"
    #   * Use F1/F2 keys to increase/reduce ahead car speed

    from os import path

    init_kwargs = {}
    # init_kwargs = {'redis_url': 'redis://localhost:6379'}
    # init_kwargs = {**init_kwargs, 'rest_host_port': args.web_server} if args.web_server else init_kwargs
    init_kwargs = {**init_kwargs, 'config_file': path.dirname(path.realpath(__file__)) + '/coordinated.yml'}

    mape.init(debug=False, **init_kwargs)
    mape.run(entrypoint=async_main())

    logger.debug('...STOP')
