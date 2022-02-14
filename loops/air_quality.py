from __future__ import annotations

import rx
import asyncio
import logging
import random
from typing import Optional, Any, Callable
from functools import reduce

import mape
from mape import Loop, operators as ops
from mape.base_elements import UID, Element
from mape.typing import Message, MapeLoop, OpsChain

from .fixitures import VirtualRoom
from .alarm import AnalyzeAVG

logger = logging.getLogger(__name__)

""" 
Air Quality is made up of two loops:
* N loops (slave) for each Monitor (air sensor) and Executor (fan actuator)
* 1 loop (master) to Analyze (AVG) and Plan. 
    This loop use rooting policy (ops.group_and_pipe(), ops.gateway()) to collect and target Messages
"""

""" LOOP MASTER DEFINITION AND CONTESTUALLY INSTANCED """
loop_master = Loop(uid='aq_master', level='1')


@loop_master.register(uid='a_avg')
class AnalyzeGroupedAVG(AnalyzeAVG):
    """ Make AVG grouped for source (ie. for each monitor)"""
    def __init__(self, loop, window_count=6, uid: str | UID = None) -> None:
        super().__init__(loop, window_count=window_count, uid=uid)
        # Update the port_out operators with the group_and_pipe
        self._p_out.operators = [ops.group_and_pipe(self._p_out.operators)]


loop_master.a_avg.debug(Element.Debug.IN | Element.Debug.OUT)


def dest_mapper(item):
    """ Find the item destination """
    # Get loop of element in src
    src_loop = mape.app[item.src].loop
    # Take the first Execute element in the loop
    execute_in_loop = [element for element in src_loop if isinstance(element, mape.base_elements.Execute)][0]
    print("dest_mapper", item.src, execute_in_loop.path)
    return execute_in_loop


@loop_master.plan(ops_out=ops.gateway(dest_mapper), param_self=True)
def p_fan(item, on_next, self):
    if self.target_air_quality > item.value:
        # Set fan speed max to 10
        item.value = min(self.target_air_quality - item.value, 10)
        on_next(item)
    else:
        item.value = 0
        on_next(item)


p_fan.debug(Element.Debug.IN | Element.Debug.OUT)
p_fan.target_air_quality = 50

loop_master.a_avg.subscribe(p_fan, scheduler=mape.rx_scheduler)
# we could put the ops.gateway() here instead on plan
# subscribe for start it (it's a plan => StartOnSubscribe)
p_fan.subscribe()

""" MAPE ELEMENTS DEFINITION """


@mape.to_monitor_cls(param_self=True)
async def Monitor(item, on_next, self: Element, something_useful=None):
    """ Simulate polling (ie read on call) """
    air_quality = self.managed_element_room.current_air_quality
    # 'dst=' not used in dest_mapper
    # 'dst=' assume the existence of an element with uid 'execute_air_quality'
    msg = Message.create(air_quality, src=self, dst=self.loop.execute_air_quality)

    await self.loop.app.k.keyspace.set('mymsg', msg)
    await self.loop.k.keyspace.set('mymsg', msg)
    await self.loop.level.k.keyspace.set('mymsg', msg)

    on_next(msg)


@mape.to_execute_cls(default_uid='execute_air_quality',
                     default_ops_in=ops.distinct_until_changed(lambda item: item.value),
                     param_self=True)
async def Execute(item, on_next, self):

    # import asyncstdlib as a
    # async for i, val in a.enumerate(self.loop.app.k.keys()):
    #     print(i, val)
    mymsg = await self.loop.app.k.keyspace.get('mymsg')
    logger.debug(mymsg)

    self.managed_element_room.set_fan(item.value)


def make(name: str, room) -> Loop:
    logger.debug(f"{'=' * 6} Init Air Quality loop {name} {'=' * 6}")

    # INSTANCE MAPE ELEMENTS
    loop = Loop(uid=name, level='0')
    m = Monitor(loop=loop)
    e = Execute(loop=loop)

    # m.debug(Element.Debug.OUT)
    e.debug(Element.Debug.IN)

    m.managed_element_room = room
    e.managed_element_room = room

    # CONNECT MAPE ELEMENTS
    # Polling, collect information each 2 seconds
    start = rx.timer(0, 2.0).pipe(
        ops.map(lambda _: Message()),
        ops.through(m),
        ops.through(loop_master.a_avg),
        # a_avg is part of master_loop already connect with its plan
        # We not need connect/subscribe to the executor due the use of gateway on plan
    ).subscribe(scheduler=mape.rx_scheduler)

    from mape.redis_remote import PubObserver
    m.subscribe(PubObserver(f"{m.path}"))
    from mape.remote.rest import POSTObserver
    m.subscribe(POSTObserver('http://0.0.0.0:6061', '/loops/rest-test/elements/executer'))

    return loop



