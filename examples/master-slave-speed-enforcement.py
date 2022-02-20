#!/usr/bin/env python3

import logging
from typing import List

import mape
from mape.utils import LogObserver, init_logger, task_exception, setdefaultattr
from mape.loop import Loop
from mape.base_elements import Element, Analyze
from mape import operators as ops
from mape.remote.redis import SubObservable
from mape.typing import Message

from examples.coordinated_common import prompt_setup

logger = init_logger()
logger.setLevel(logging.DEBUG)

mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


class AVG(Analyze):
    def __init__(self, loop, window_count=6, uid: str = 'avg') -> None:
        ops_out_avg = (
            ops.window_with_count(count=window_count),
            ops.flat_map(
                lambda window: window.pipe(
                    ops.to_list(),
                    ops.map(self._compute_avg_msg)
                )
            )
        )

        super().__init__(loop, uid, ops_out=ops_out_avg)

    @staticmethod
    def _compute_avg_msg(items: List[Message]):
        from functools import reduce
        items_sum = reduce(lambda acc, item: acc + item.value, items, 0)

        from copy import deepcopy
        avg_msg = deepcopy(items[0])

        avg_msg.value = items_sum / len(items)
        return avg_msg


async def create_speed_enforcement_loop():
    loop = Loop(uid='speed_enforcement')

    @loop.register(uid='avg')
    class GroupedAVG(AVG):
        def __init__(self, loop, window_count=6, uid=None) -> None:
            super().__init__(loop, window_count=window_count, uid=uid)
            # Update the port_out operators with the group_and_pipe
            self._p_out.operators = [ops.group_and_pipe(self._p_out.operators)]

    loop.avg.debug(Element.Debug.OUT)

    @loop.plan(ops_out=ops.router(), param_self=True)
    def penalty(item, on_next, self):
        delta_speed = item.value - self.speed_threshold

        if delta_speed > self.speed_threshold * 0.6:
            item.value = 0
            on_next(item)
        elif delta_speed > self.speed_threshold * 0.3:
            item.value = 30
            on_next(item)

    penalty.speed_threshold = 150

    loop.avg.subscribe(penalty)
    penalty.subscribe()


async def create_car_loop(name, init_speed):
    from examples.fixtures import VirtualCar

    # Managed elements
    car = VirtualCar(name, speed=init_speed)
    # Stdin/key bindings setup for user input
    # prompt_setup(car)

    """ MAPE Loop and elements definition """
    loop = Loop(uid=f"car_{name}")

    @loop.monitor(
        ops_out=ops.sample(6, scheduler=mape.rx_scheduler),
        param_self=True)
    def mon(item, on_next, self):
        if 'speed' in item:
            on_next(Message.create(value=item['speed'], src=self, dst=self.loop.exec))

    @loop.execute
    def exec(item: Message, on_next):
        car.speed_limit = item.value

    mon.debug(Element.Debug.OUT)

    mon.subscribe(mape.app.speed_enforcement.avg)

    # Starting monitor...
    logger.info(f"{mon} element started")
    mon.start()

    car.set_callback('speed', mon)


async def async_main():
    await create_speed_enforcement_loop()

    await create_car_loop('Veyron', 300)
    await create_car_loop('Countach', 190)
    await create_car_loop('Panda', 90)


if __name__ == '__main__':
    logger.debug('START...')

    mape.init(debug=False)
    mape.run(entrypoint=async_main())

    logger.debug('...STOP')
