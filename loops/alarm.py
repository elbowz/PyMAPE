from __future__ import annotations

import rx
import asyncio
import logging
import random
from typing import Optional, Any, Callable
from functools import reduce

import mape
from mape import Loop, operators as ops, MapeLoop, OpsChain
from mape.base_elements import UID, Element
from mape.typing import Message

from .fixitures import VirtualRoom

logger = logging.getLogger(__name__)

""" 
Air Quality is made up of two loops:
* N loops (slave) for each Monitor (air sensor) and Executor (fan actuator)
* 1 loop (master) to Analyze (AVG) and Plan. 
    This loop use rooting policy (ops.group_and_pipe(), ops.gateway()) to collect and target Messages
"""

""" LOOP ALARM DEFINITION AND CONTESTUALLY INSTANCED """
loop_alarm = Loop(uid='alarm')


@loop_alarm.register(uid='a_avg')
class AnalyzeAVG(mape.base_elements.Analyze):
    def __init__(self, loop, window_count=6, uid: str = 'AnalyzeAVG') -> None:
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

    def _compute_avg_msg(self, items):
        items_sum = reduce(lambda acc, item: acc + item.value, items, 0)

        # Keep src and timestamp from first Message in items
        msg = {
            'value': items_sum / len(items),
            'src': items[0].src,
            'dst': items[0].dst,
            'timestamp': items[0].timestamp
        }

        return Message(**msg)


@loop_alarm.plan(uid='plan_alarm', param_self=True)
def plan(item, on_next, self):
    item.value = True if item.value > self.threshold_air_quality else False
    on_next(item)


@loop_alarm.execute(uid='execute_alarm',
                    ops_in=ops.distinct_until_changed(lambda item: item.value),
                    param_self=True)
def execute(item, on_next, self):
    logger.info(f"AVG Alarm {self.path} set to {'ON' if item.value else 'OFF'}")


loop_alarm.a_avg.debug(Element.Debug.IN | Element.Debug.OUT)
plan.threshold_air_quality = 60

loop_alarm.a_avg.subscribe(plan)
plan.subscribe(execute)


def make():
    logger.debug(f"{'=' * 6} Init Air Quality Alarm loop {'=' * 6}")

    # Find all the loop for Air Quality ('aq_') and Monitor belong to them
    for loop in mape.app:
        if loop.uid.startswith('aq_'):
            if 'Monitor' in loop:
                loop['Monitor'].subscribe(loop_alarm.a_avg)
