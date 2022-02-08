import asyncio
import aioredis
import pickle

import rx
from rx.subject import Subject
from rx.core import Observer, Observable
from rx.disposable import Disposable, CompositeDisposable
from rx import operators as ops

from dataclasses import dataclass, field
from typing import Type, Any, List, Tuple, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple

from .base_elements import Port


def _serializer(item):
    print(item)
    # try:
    return pickle.dumps(item, pickle.HIGHEST_PROTOCOL)
    # except Exception as e:
    #     print("no no", e)
    # return json.dumps(item, default=lambda obj: obj.__dict__)


# TODO:
#  * add deserializer
#  * remove port from RedisPublishObserver?!


_redis = aioredis.from_url("redis://localhost")


class RedisPublishObserver(Observer):

    def __init__(self, channel, redis=None) -> None:
        self._channel = channel
        self._queue = asyncio.Queue()
        self._redis = redis or _redis or aioredis.from_url("redis://localhost")

        self._p_in = Port(input=Subject(), operators=[ops.materialize()])
        self._p_in.pipe = self._p_in.input.pipe(*self._p_in.operators)
        self._p_in.disposable = self._p_in.pipe.subscribe(on_next=lambda item: self._publish(item))

        asyncio.create_task(self._publish_queue())

        super().__init__(self._p_in.input.on_next, self._p_in.input.on_error, self._p_in.input.on_completed)

    def _publish(self, item):
        self._queue.put_nowait(item)

    async def _publish_queue(self):
        while True:
            item = await self._queue.get()
            await self._redis.publish(self._channel, _serializer(item))

    def dispose(self) -> None:
        self._task.cancel()
        self._p_in.disposable.dispose()

    def __del__(self):
        self.dispose()


class RedisSubscribeObservable(Observable):
    def __init__(self, channels_patterns, redis=None) -> None:
        self._redis = redis or _redis or aioredis.from_url("redis://localhost")
        self._pubsub = None
        self._channels_pattern = channels_patterns if isinstance(channels_patterns, List) else [channels_patterns]
        self._disposable = CompositeDisposable()

        def on_subscribe(observer, scheduler):
            print("subscribe")

            def _on_publish(message):
                item = pickle.loads(message['data'])
                observer.on_next(item)

            async def init_redis_sub():
                self._pubsub = self._redis.pubsub()

                patterns_callbacks = {pattern: _on_publish for pattern in self._channels_pattern}
                await self._pubsub.psubscribe(**patterns_callbacks)
                await self._pubsub.run()

            task = asyncio.create_task(init_redis_sub())
            self._disposable.add(Disposable(lambda: task.cancel()))

            return Disposable(lambda: asyncio.create_task(self.unsubscribe()))

        self._auto_connect = rx.create(on_subscribe).pipe(ops.dematerialize(), ops.share())
        super().__init__()

    def _subscribe_core(self, observer, scheduler=None):
        return self._auto_connect.subscribe(observer, scheduler=scheduler)

    async def unsubscribe(self):
        await self._pubsub.unsubscribe(*self._channels_pattern)
        self._disposable.dispose()

    def __del__(self):
        self.unsubscribe()
