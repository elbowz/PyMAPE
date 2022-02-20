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


async def async_main(car_name, init_speed, ambulance_dest=None, cars_dst=None):
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

    emergency_detect_out = emergency_detect.pipe(
        # Only when local state change
        ops.distinct_until_changed(),
        ops.filter(lambda emergency: emergency is True)
    )

    analyzer_out = analyzer.pipe(
        # Only when local state change
        ops.distinct_until_changed(lambda item: item.value)
    )

    """ MAPE Elements REMOTE connection """

    if not ambulance_dest:
        emergency_detect_out.subscribe(PubObserver(emergency_detect.path))
    else:
        ambulance_emergency_policy = POSTObserver(f"http://{ambulance_dest}", 'ambulance_emergency.emergency_policy')
        emergency_detect_out.subscribe(ambulance_emergency_policy)

    if not cars_dst:
        # Listen/Subscribe for others cars analyzer output
        # notes: for clarity can be used "safety_policy.port_in" and "analyzer.uid"
        SubObservable(f"car_*_safety.{analyzer}").pipe(
            ops.filter(lambda item: item.src != analyzer.path)
        ).subscribe(analyzer)

        # Send/Publish the analyzer output to others cars (for clarity can be used "analyzer.port_out")
        analyzer_out.subscribe(PubObserver(analyzer.path))
    else:
        # Send stream to elements through a POST request
        for host in cars_dst:
            host, car_name = host.split('/')
            dest_safety_policy = POSTObserver(f"http://{host}", f"car_{car_name}_safety.{analyzer}")

            analyzer_out.subscribe(dest_safety_policy)

    # Starting monitor...
    logger.info(f"{emergency_detect} element started")
    emergency_detect.start()

    # Stdin/key bindings setup for user input
    prompt_setup(car)


def prompt_setup(vehicle):
    from examples.utils import handle_prompt

    def prompt_handler(value):
        if value in ['exit', 'close', 'stop']:
            mape.stop()

    def key_emergency(key):
        if key == 'f1':
            vehicle.emergency_detect = True
        elif key == 'f2':
            vehicle.emergency_detect = False

    def key_close_handler(key):
        mape.stop()

    key_bindings_handlers = {'f1': key_emergency, 'f2': key_emergency, 'c-c': key_close_handler}
    asyncio.create_task(task_exception(handle_prompt(prompt_handler, key_bindings_handlers)))


if __name__ == '__main__':
    logger.debug('START...')

    # CLI EXAMPLES
    # Redis:
    # * python -m examples.coordinated-car-with-message --name Veyron --speed 380
    # REST:
    # 1. python -m examples.coordinated-car-with-message --name Veyron --speed 380 --web-server 0.0.0.0:6060 --ambulance 0.0.0.0:6000 --cars 0.0.0.0:6061/Countach 0.0.0.0:6062/Panda
    # 2. python -m examples.coordinated-car-with-message --name Countach --speed 240 --web-server 0.0.0.0:6061 --ambulance 0.0.0.0:6000 --cars 0.0.0.0:6060/Veyron 0.0.0.0:6062/Panda
    # 3. python -m examples.coordinated-car-with-message --name Panda --speed 90 --web-server 0.0.0.0:6062 --ambulance 0.0.0.0:6000 --cars 0.0.0.0:6060/Veyron 0.0.0.0:6061/Countach

    import argparse
    parser = argparse.ArgumentParser(description='MAPE Loop')
    parser.add_argument('-n', '--name', type=str, metavar='CAR_NAME', required=True)
    parser.add_argument('-s', '--speed', type=int, metavar='CAR_SPEED', default=80)
    parser.add_argument('-w', '--web-server', type=str, metavar='HOST_PORT')
    parser.add_argument('-a', '--ambulance', type=str, metavar='HOST_PORT')
    parser.add_argument('-c', '--cars', type=str, nargs='*', metavar='HOST_PORT/CAR_NAME')
    args = parser.parse_args()

    init_kwargs = {'redis_url': 'redis://localhost:6379'}
    init_kwargs = {**init_kwargs, 'rest_host_port': args.web_server} if args.web_server else init_kwargs

    run_kwargs = {
        'car_name': args.name,
        'init_speed': args.speed,
        'ambulance_dest': args.ambulance,
        'cars_dst': args.cars
    }

    mape.init(debug=False, **init_kwargs)
    mape.run(entrypoint=async_main(**run_kwargs))

    logger.debug('...STOP')
