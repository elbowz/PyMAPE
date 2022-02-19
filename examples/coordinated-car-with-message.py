#!/usr/bin/env python3

import random
import sys
import logging
import asyncio

from pydantic import BaseModel

import mape
from mape.utils import LogObserver, init_logger, task_exception, setdefaultattr
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
    from examples.fixtures import VirtualCar

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

    @loop.analyze(param_self=True)
    def analyzer(item, on_next, self):
        setdefaultattr(self, 'analyzer_msg_from', {})

        if isinstance(item, Message):
            # Item/packet come from other loops (Message)

            if self.analyzer_msg_from.get(item.src, None) == item.value:
                return

            self.analyzer_msg_from[item.src] = item.value

            logger.info(list(self.analyzer_msg_from.items()))
            count_true = list(self.analyzer_msg_from.values()).count(True)

            if count_true >= self.emergency_car_threshold:
                on_next(Message.create(True, src=self))
            elif count_true <= 0:
                on_next(Message.create(False, src=self))
        else:
            # Item/packet come from emergency_detect
            if item is False:
                self.analyzer_msg_from.clear()

            on_next(Message.create(item, src=self))

    analyzer.emergency_car_threshold = 2

    @loop.plan(ops_in=ops.distinct_until_changed(lambda item: item.value), param_self=True)
    async def safety_policy(item, on_next, self):
        if item.value is True:
            self.last_speed_limit = self.loop.k.speed_limit
            new_speed = min(self.last_speed_limit, self.safety_speed)

            on_next(SpeedItem(value=new_speed))
            on_next({'hazard_lights': True})
        else:
            last_speed_limit = setdefaultattr(self, 'last_speed_limit', self.loop.k.speed_limit)
            on_next(SpeedItem(value=last_speed_limit))
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
        # Only when local state change
        ops.distinct_until_changed(lambda item: item.value)
    )

    """ MAPE Elements REMOTE connection """

    if not elements_dest:
        # Listen/Subscribe for others cars analyzer output
        # notes: for clarity can be used "safety_policy.port_in" and "analyzer.uid"
        SubObservable(f"car_*_safety.{analyzer}").pipe(
            ops.filter(lambda item: item.src != analyzer.path)
        ).subscribe(analyzer)

        # Send/Publish the analyzer output to others cars (for clarity can be used "analyzer.port_out")
        analyzer_out.subscribe(PubObserver(analyzer.path))
    else:
        # Send stream to elements through a POST request
        for host in elements_dest:
            host, car_name = host.split('/')
            dest_safety_policy = POSTObserver(f"http://{host}", f"car_{car_name}_safety.{analyzer}")

            analyzer_out.subscribe(dest_safety_policy)

    # Starting monitor...
    logger.info(f"{emergency_detect} element started")
    emergency_detect.start()

    # Stdin/key bindings setup for user input
    prompt_setup(car)


def prompt_setup(car):
    from examples.utils import handle_prompt

    def prompt_handler(value):
        if value in ['exit', 'close', 'stop']:
            mape.stop()

    def key_emergency(key):
        if key == 'f1':
            car.emergency_detect = True
        elif key == 'f2':
            car.emergency_detect = False

    def key_close_handler(key):
        mape.stop()

    key_bindings_handlers = {'f1': key_emergency, 'f2': key_emergency, 'c-c': key_close_handler}
    asyncio.create_task(task_exception(handle_prompt(prompt_handler, key_bindings_handlers)))


if __name__ == '__main__':
    logger.debug('START...')

    run_kwargs = {'car_name': sys.argv[1], 'init_speed': int(sys.argv[2])}

    if len(sys.argv) <= 3:
        # "python -m examples.test-coordinated-car-with-message Bugatti 120"
        init_kwargs = {'redis_url': 'redis://localhost:6379'}
    else:
        # 1. "python -m examples.test-coordinated-car-with-message Bugatti 380 0.0.0.0:6060 0.0.0.0:6061/Panda 0.0.0.0:6062/Countach"
        # 2. "python -m examples.test-coordinated-car-with-message Panda 120 0.0.0.0:6061 0.0.0.0:6060/Bugatti 0.0.0.0:6062/Countach"
        # 3. "python -m examples.test-coordinated-car-with-message Countach 260 0.0.0.0:6062 0.0.0.0:6060/Bugatti 0.0.0.0:6061/Panda"
        init_kwargs = {'rest_host_port': sys.argv[3]}
        run_kwargs.update({'elements_dest': sys.argv[4:]})

    mape.init(debug=False, **init_kwargs)
    mape.run(entrypoint=async_main(**run_kwargs))

    logger.debug('...STOP')
