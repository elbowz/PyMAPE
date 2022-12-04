from __future__ import annotations

import asyncio
import logging
import aioredis
from functools import partial

import rx
from rx.subject import Subject
from rx.core import Observer, Observable
from rx.disposable import Disposable
from rx import operators as ops

from typing import List

import mape
from mape.base_elements import Port
from mape.utils import log_task_exception
from .pubsub import subscribe_handler
from ..de_serializer import obj_to_raw, Pickled

logger = logging.getLogger(__name__)


class PubObserver(Observer):

    def __init__(self, channel, redis=None, serializer=None) -> None:
        self._channel = channel
        self._queue = asyncio.Queue()
        self._redis = redis or mape.redis
        self._serializer = serializer or partial(obj_to_raw, Pickled)

        if not isinstance(self._redis, aioredis.Redis):
            logger.error("You are trying to use Redis without config it!")

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


