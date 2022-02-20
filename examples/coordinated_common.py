#!/usr/bin/env python3

import asyncio

import mape
from mape.utils import task_exception
from mape.base_elements import to_monitor_cls


@to_monitor_cls(default_uid='emergency_detect', param_self=True)
def emergency_detect_cls(item, on_next, self):
    if 'speed' in item:
        # Local volatile knowledge
        self.loop.k.current_speed = item['speed']
    elif 'speed_limit' in item:
        self.loop.k.speed_limit = item['speed_limit']
    elif 'emergency_detect' in item:
        on_next(item['emergency_detect'])


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
