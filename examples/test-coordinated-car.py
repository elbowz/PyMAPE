#!/usr/bin/env python3

import random
import sys
import logging
import asyncio

from pydantic import BaseModel

import mape
from mape.utils import LogObserver, init_logger
from mape.loop import Loop
from mape.base_elements import Element
from mape import operators as ops
from mape.remote.redis import SubObservable, PubObserver
from mape.remote.rest import POSTObserver
from mape.typing import Message

logger = init_logger()
logger.setLevel(logging.DEBUG)

mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


class SpeedItem(BaseModel):
    value: int = 0


async def async_main(car_name, init_speed, elements_dest=None):
    from loops.fixitures import VirtualCar

    # Managed elements
    car = VirtualCar(car_name, init_speed)

    """ MAPE Loop and elements definition """
    loop = Loop(uid=f"car_{car_name}_safety")

    @loop.monitor(param_self=True)
    def emergency_detect(item, on_next, self):
        if 'speed' in item:
            # Local volatile knowledge
            self.loop.k.current_speed = item['speed']
        elif 'speed_limit' in item:
            self.loop.k.speed_limit = item['speed_limit']
        elif 'emergency_detect' in item:
            on_next(item['emergency_detect'])

    car.set_callback('speed', emergency_detect)
    car.set_callback('speed_limit', emergency_detect)
    car.set_callback('emergency_detect', emergency_detect)

    @loop.analyze
    def analyzer(emergency_detect: bool, on_next):
        on_next(emergency_detect)

    @loop.plan(ops_in=ops.distinct_until_changed(), param_self=True)
    async def safety_policy(safety_state, on_next, self):
        if safety_state is True:
            self.last_speed_limit = self.loop.k.speed_limit
            new_speed = min(self.last_speed_limit, self.safety_speed)

            on_next(SpeedItem(value=new_speed))
            on_next({'hazard_lights': True})
        else:
            on_next(SpeedItem(value=self.last_speed_limit))
            on_next({'hazard_lights': False})

    safety_policy.safety_speed = 30

    @loop.execute(ops_in=ops.filter(lambda item: isinstance(item, SpeedItem)))
    def speed_limit(item: SpeedItem, on_next):
        car.speed_limit = item.value

    @loop.execute(ops_in=ops.filter(lambda item: 'hazard_lights' in item))
    def hazard_lights(item: dict, on_next):
        car.hazard_lights = item['hazard_lights']

    # for element in loop:
    #     element.debug(Element.Debug.IN)

    """ MAPE Elements LOCAL connection """
    emergency_detect.subscribe(analyzer)
    analyzer.subscribe(safety_policy)
    safety_policy.subscribe(speed_limit)
    safety_policy.subscribe(hazard_lights)

    analyzer_out = analyzer.pipe(
        # Only when hazard_lights are ON
        ops.filter(lambda hazard_lights: hazard_lights is True)
    )

    """ MAPE Elements REMOTE connection """

    if not elements_dest:
        # Listen/Subscribe for others cars analyzer output
        # notes: for clarity can be used "safety_policy.port_in" and "analyzer.uid"
        SubObservable(f"car_*_safety.{analyzer}").subscribe(safety_policy)

        # Send/Publish the analyzer output to others cars (for clarity can be used "analyzer.port_out")
        analyzer_out.subscribe(PubObserver(analyzer.path))
    else:
        # Send stream to elements through a POST request
        for host in elements_dest:
            host, car_name = host.split('/')
            dest_safety_policy = POSTObserver(f"http://{host}", f"car_{car_name}_safety.{safety_policy}")

            analyzer_out.subscribe(dest_safety_policy)

    # Starting monitor...
    logger.info(f"{emergency_detect} element started")
    emergency_detect.start()

    # Manage shortcuts/hotkeys
    asyncio.create_task(catch_single_key_press(car))


async def catch_single_key_press(car):
    from prompt_toolkit.input import create_input
    from prompt_toolkit.keys import Keys

    done = asyncio.Event()
    input = create_input()

    def keys_ready():
        for key_press in input.read_keys():
            if key_press.key == '1':
                car.emergency_detect = True
            elif key_press.key == '0':
                car.emergency_detect = False
            elif key_press.key == Keys.ControlC:
                done.set()

    with input.raw_mode():
        with input.attach(keys_ready):
            await done.wait()


if __name__ == '__main__':
    logger.debug('START...')

    run_kwargs = {'car_name': sys.argv[1], 'init_speed': int(sys.argv[2])}

    if len(sys.argv) <= 3:
        # "python -m examples.test-coordinated-car Bugatti 120"
        init_kwargs = {'redis_url': 'redis://localhost:6379'}
    else:
        # 1. "python -m examples.test-coordinated-car Bugatti 380 0.0.0.0:6060 0.0.0.0:6061/Panda 0.0.0.0:6062/Countach"
        # 2. "python -m examples.test-coordinated-car Panda 120 0.0.0.0:6061 0.0.0.0:6060/Bugatti 0.0.0.0:6062/Countach"
        # 3. "python -m examples.test-coordinated-car Countach 260 0.0.0.0:6062 0.0.0.0:6060/Bugatti 0.0.0.0:6061/Panda"
        init_kwargs = {'rest_host_port': sys.argv[3]}
        run_kwargs.update({'elements_dest': sys.argv[4:]})

    mape.init(debug=False, **init_kwargs)
    mape.run(entrypoint=async_main(**run_kwargs))

    logger.debug('...STOP')
