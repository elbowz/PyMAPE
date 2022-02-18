from __future__ import annotations

import asyncio
from functools import partial
from typing import List, Dict, Callable

import mape
from mape.remote.de_serializer import obj_from_raw, Pickled
from mape.utils import log_task_exception


def subscribe_handler_deco(channels_patterns, full_message=False, deserializer=None, redis=None):
    channels_patterns = channels_patterns if isinstance(channels_patterns, List) else [channels_patterns]

    def decorator(func):
        sub_handlers = {pattern: func for pattern in channels_patterns}
        task = subscribe_handler(sub_handlers, full_message, deserializer, redis)

        func.task = task
        func.cancel = task.cancel
        return func

    return decorator


def subscribe_handler(sub_handlers: Dict[str, Callable], full_message=False, deserializer=None, redis=None):
    redis = redis or mape.redis
    deserializer = deserializer or partial(obj_from_raw, Pickled)

    def _on_publish(message, callback):
        message['data'] = deserializer(message['data'])
        callback(message if full_message else message['data'])

    def on_cancel(_):
        sub_channels = sub_handlers.keys()
        asyncio.create_task(pubsub.unsubscribe(sub_channels))

    @log_task_exception
    async def init_redis_sub():
        patterns_callbacks = {pattern: partial(_on_publish, callback=handler) for pattern, handler in
                              sub_handlers.items()}
        await pubsub.psubscribe(**patterns_callbacks)
        await pubsub.run()

    pubsub = redis.pubsub()
    task = asyncio.create_task(init_redis_sub())
    task.add_done_callback(on_cancel)
    return task
