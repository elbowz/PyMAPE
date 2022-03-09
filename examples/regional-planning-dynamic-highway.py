#!/usr/bin/env python3

import logging
import asyncio
from typing import Any, Optional, Callable

from pydantic import BaseModel

import mape
from mape.utils import init_logger, task_exception
from mape.loop import Loop
from mape.base_elements import Plan
from mape import operators as ops
from mape.typing import Message
from mape.remote.influxdb import InfluxObserver

logger = init_logger()
logger.setLevel(logging.DEBUG)

mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


class Car(BaseModel):
    name: str
    action: str


async def create_lane(number, k_cars, cars_generator):
    carriageway = cars_generator.uid

    """ MAPE Loop and elements definition """
    loop = Loop(uid=f"lane_{number}")

    @loop.monitor
    def car_mon(car, on_next):
        # Payload transform (Dict => Object)
        action = list(car.keys())[0]
        on_next(Car(action=action, name=car[action]))

    @loop.analyze
    async def cars_store(car, on_next, self):
        # Avoid "concurrent" add/remove in Redis set
        async with self.lock:
            if 'enter' in car.action:
                # Add new car to Set in global K
                await self.k_cars.add(car.name)
            elif 'exit' in car.action:
                # Remove car from Set in global K
                await self.k_cars.remove(car.name)

            car_count = await self.k_cars.len()
            logger.debug(f"{self.loop.uid: <6} | {car.action[:-2]: <5} | {car.name: <12} | {car_count:>3} (tot)")
            # cars = [car async for car in self.k_cars.values()]
            # logger.debug(f"{await self.k_cars.len()} cars in '{self.loop}'")

            on_next(car_count)

    cars_store.k_cars = k_cars
    cars_store.lock = asyncio.Lock()

    @loop.execute
    def set_lane(lanes: Message, on_next, self):
        cars_generator.lanes = lanes.value

    car_mon.subscribe(cars_store)
    # Use InfluxDB sink/terminator to store number of cars and lanes
    cars_store.subscribe(InfluxObserver(tags=('type', f"cars_{carriageway}")))

    # Starting monitor...
    logger.info(f"{car_mon.path} element started")
    car_mon.start()

    # Register handlers
    cars_generator.set_callback(f"enter_{number}", car_mon)
    cars_generator.set_callback(f"exit_{number}", car_mon)


async def async_main(name, count_lanes):
    opposite_carriageway = f"carriageway_{'up' if name == 'down' else 'down'}"

    """ MAPE Loop and elements definition """
    loop = Loop(uid=f"carriageway_{name}")

    class Lanes(Plan):
        def __init__(self, loop, opposite_carriageway, max_lanes=8, uid=None):
            super().__init__(loop, uid, ops_out=(
                ops.distinct_until_changed(lambda item: item.value),
                ops.router()
            ))

            self.max_lanes = max_lanes
            # Get access to Sets (up and down) in the global K
            self.k_cars = self.loop.app.k.create_set(f"{self.loop}_cars", str)
            self.k_cars_opposite = self.loop.app.k.create_set(f"{opposite_carriageway}_cars", str)

            # Register handler for add (sadd) / remove (srem) cars
            self.loop.app.k.notifications(self._on_cars_change,
                                          f"carriageway_*_cars",
                                          cmd_filter=('sadd', 'srem'))

        async def _on_cars_change(self, message):
            # Count cars in Sets
            cars = await self.k_cars.len()
            opposite_cars = await self.k_cars_opposite.len()
            tot = cars + opposite_cars

            # Compute current highway number of lanes
            if tot:
                lanes = round(self.max_lanes / tot * cars)

                if lanes == 0:
                    lanes = lanes if cars == 0 else 1
                elif lanes == 8:
                    lanes = lanes if opposite_cars == 0 else 7

                # Send to the lane executer (lane_{number}.set_lane)
                dst_path = f"lane_{max(0, lanes-1)}.set_lane"
                self._on_next(Message.create(lanes, src=self, dst=dst_path))

    # Instance lanes planner
    lanes = Lanes(loop, opposite_carriageway, max_lanes=count_lanes, uid='lanes')

    """ MAPE Elements LOCAL connection """
    lanes.subscribe(InfluxObserver())

    # Create Set in the global Knowledge
    k_cars = mape.app.k.create_set(f"{loop}_cars", str)
    # Clean Set before each start
    await k_cars.clear()

    # Managed elements
    from examples.fixtures import VirtualCarGenerator
    cars_generator = VirtualCarGenerator(loop.uid, auto_generation=False, lanes=count_lanes)
    # Stdin/key bindings setup for user input
    prompt_setup(cars_generator)

    # Create road lanes
    for number in range(count_lanes):
        await create_lane(number, k_cars, cars_generator)


def prompt_setup(cars_generator):
    from examples.utils import handle_prompt

    def prompt_handler(value):
        if value in ['exit', 'close', 'stop']:
            mape.stop()

    def key_enter_exit(key):
        if key == 'f1':
            cars_generator.add_random_cars(count=1)
        elif key == 'f2':
            cars_generator.remove_random_cars(count=1)

    def key_close_handler(key):
        mape.stop()

    key_bindings_handlers = {'f1': key_enter_exit, 'f2': key_enter_exit, 'c-c': key_close_handler}
    asyncio.create_task(task_exception(handle_prompt(prompt_handler, key_bindings_handlers)))


if __name__ == '__main__':
    logger.debug('START...')

    # CLI EXAMPLES
    # Redis:
    # * python -m examples.regional-planning-dynamic-highway --name up --lanes 8
    # * python -m examples.regional-planning-dynamic-highway --name down --lanes 8

    import argparse
    parser = argparse.ArgumentParser(description='MAPE Loop')
    parser.add_argument('-n', '--name', type=str, metavar='NAME', required=True)
    parser.add_argument('-l', '--lanes', type=int, metavar='LANES', default=4)
    args = parser.parse_args()

    init_kwargs = {'redis_url': 'redis://localhost:6379'}
    init_kwargs = {**init_kwargs, 'config_file': 'examples/coordinated.yml'}

    run_kwargs = {
        'name': args.name,
        'count_lanes': args.lanes,
    }

    mape.init(debug=False, **init_kwargs)
    mape.run(entrypoint=async_main(**run_kwargs))

    logger.debug('...STOP')
