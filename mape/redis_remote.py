import asyncio
import aioredis
import pickle
from functools import partial, wraps

import rx
from rx.subject import Subject
from rx.core import Observer, Observable
from rx.disposable import Disposable, CompositeDisposable
from rx import operators as ops

from typing import Type, Any, List, Dict, Tuple, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple

import mape
from .base_elements import Port
from .utils import log_task_exception


def _serializer(obj):
    return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)


def _deserializer(raw):
    return pickle.loads(raw)


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
    deserializer = deserializer or _deserializer

    def _on_publish(message, callback):
        message['data'] = deserializer(message['data'])
        callback(message if full_message else message['data'])

    def _on_cancel(_):
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
    task.add_done_callback(_on_cancel)
    return task


class PubObserver(Observer):

    def __init__(self, channel, redis=None, serializer=None) -> None:
        self._channel = channel
        self._queue = asyncio.Queue()
        self._redis = redis or mape.redis
        self._serializer = serializer or _serializer

        self._p_in = Port(input=Subject(), operators=[ops.materialize()])
        self._p_in.pipe = self._p_in.input.pipe(*self._p_in.operators)
        self._p_in.disposable = self._p_in.pipe.subscribe(on_next=lambda item: self._publish(item))

        self._task = asyncio.create_task(self._publish_queue())

        super().__init__(self._p_in.input.on_next, self._p_in.input.on_error, self._p_in.input.on_completed)

    def _publish(self, item):
        self._queue.put_nowait(item)

    @log_task_exception
    async def _publish_queue(self):
        while True:
            item = await self._queue.get()
            await self._redis.publish(self._channel, self._serializer(item))

    def dispose(self) -> None:
        self._task.cancel()
        self._p_in.disposable.dispose()

    def __del__(self):
        self.dispose()


class SubObservable(Observable):
    def __init__(self, channels_patterns, deserializer=None, redis=None) -> None:
        self._channels_pattern = channels_patterns if isinstance(channels_patterns, List) else [channels_patterns]
        self._task = None

        def on_subscribe(observer, scheduler):
            sub_handlers = {pattern: observer.on_next for pattern in self._channels_pattern}
            self._task = subscribe_handler(sub_handlers, full_message=False, deserializer=deserializer, redis=redis)

            return Disposable(self.unsubscribe)

        self._auto_connect = rx.create(on_subscribe).pipe(ops.dematerialize(), ops.share())
        super().__init__()

    def _subscribe_core(self, observer, scheduler=None):
        return self._auto_connect.subscribe(observer, scheduler=scheduler)

    def unsubscribe(self):
        self._task.cancel()

    def __del__(self):
        self.unsubscribe()
