from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional

import mape
from mape import Loop, operators as ops
from mape.base_elements import UID, Element
from mape.utils import log_task_exception
from mape.typing import Message, MapeLoop, OpsChain

from .fixitures import VirtualRoom

logger = logging.getLogger(__name__)


""" MAPE ELEMENTS DEFINITION """


class Monitor(mape.base_elements.Monitor):
    def __init__(self,
                 room: VirtualRoom,
                 loop: MapeLoop, uid: str | UID = None,
                 ops_in: Optional[OpsChain] = (),
                 ops_out: Optional[OpsChain] = ()
                 ) -> None:
        """ The constructor override is not mandatory,
            we could inject 'managed_element_room' directly with an 'obj.attr = ...' """
        self.task = None
        self.managed_element_room = room
        super().__init__(loop, uid, ops_in, ops_out)

    @log_task_exception
    async def _read_loop(self, interval=6):
        """ Simulate callback """
        while True and self.is_running:
            # item = Message(value=self.managed_element_room.current_temperature, src=self.path)
            item = self.managed_element_room.current_temperature

            await self.loop.app.k.keyspace.set('mymsg', item)
            await self.loop.k.keyspace.set('mymsg', item)
            await self.loop.level.k.keyspace.set('mymsg', item)

            self._on_next(item)
            await asyncio.sleep(random.randint(1, 10))

    def start(self, scheduler=None):
        disposable = super().start(scheduler=scheduler)

        # TODO: create a on_start() and wrap with asyncio.lock?!
        aioloop = mape.aio_loop or asyncio.get_event_loop()
        self.task = aioloop.create_task(self._read_loop(interval=6))

        return disposable

    def stop(self):
        super().stop()
        self.task.cancel()

    def test_call_method(self, args0, args1, kwargs0, kwargs1=None):
        logger.debug(f"I'm {self.uid}.test_call_method(), called with {args0}, {args1}, {kwargs0}, {kwargs1}")


@mape.to_plan_cls(default_ops_in=ops.debounce(5.0), param_self=True)
def Plan(item, on_next, self):
    # item.value = True if item.value < self.target_temp else False
    item = True if item < self.target_temp else False
    on_next(item)


@mape.to_execute_cls(default_uid=UID.RANDOM,
                     default_ops_in=ops.distinct_until_changed(),
                     param_self=True)
async def Execute(item, on_next, self, useful_params=None):
    logger.debug(f"I'm {self.uid}, called with useful_params='{useful_params}'")
    # self.managed_element_room.set_heater(item.value)
    self.managed_element_room.set_heater(item)

    return item


def make(name: str, target_temp: float, room) -> Loop:
    logger.debug(f"{'=' * 6} Init Thermostat loop {name} {'=' * 6}")

    # INSTANCE MAPE ELEMENTS
    loop = Loop(uid=name)
    m = Monitor(room, loop=loop, uid=UID.DEF)
    p = Plan(loop=loop, uid=f"plan4{name}")
    e = Execute(loop=loop)

    m.debug(Element.Debug.IN)
    p.debug(Element.Debug.IN | Element.Debug.OUT)
    e.debug(Element.Debug.IN)

    p.target_temp = target_temp
    e.managed_element_room = room

    # CONNECT MAPE ELEMENTS
    # monitor.pipe(
    #     mape_ops.through(p),
    #     mape_ops.through(e)
    # ).subscribe()
    # ... or
    m.subscribe(p, scheduler=mape.rx_scheduler)
    p.subscribe(e, scheduler=mape.rx_scheduler)

    return loop



