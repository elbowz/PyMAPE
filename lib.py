import time
import random
import asyncio
from functools import singledispatch
from threading import current_thread
from typing import Optional, Union, Any, Awaitable, Callable, Coroutine

import rx
import rx.operators as ops
from rx.core import typing
from rx.scheduler.eventloop import AsyncIOScheduler
from rx.disposable import Disposable, CompositeDisposable
from rx.subject import Subject

""" FIXITURES """

temp_a = iter((18, 19, 18, 19, 20, 21, 20, 7, 18, 14, 10, 12, 6, 8, 6, 5, 6, 9, 5))
temp_b = iter((18, 19, 18, 19, 20, 21, 23, 22, 18, 16, 14, 12, 10, 8, 7, 5, 6, 9, 10))


class VirtualRoom:
    def __init__(self, init_temperature: int) -> None:
        self.heater_state = False
        self.current_temperature = init_temperature

    def tick(self):
        tick_value = random.uniform(0, 1)

        if self.heater_state:
            self.current_temperature += tick_value
        else:
            self.current_temperature -= tick_value

    def set_heater(self, state: bool):
        self.heater_state = state


""" UTILS """

start = time.time()


def log(value: str):
    print(f"{time.time() - start:.3f} {current_thread().name} {value}")


class ShareMem:
    def __setattr__(self, key, value):
        log(f"shared_mem: {key} = {value}")
        return super().__setattr__(key, value)

    def __getattribute__(self, key):
        return super().__getattribute__(key)

    def setdefault(self, key, value):
        if not hasattr(self, key):
            setattr(self, key, value)
        return getattr(self, key)


""" OPERATORS """


def map_async(coro: Callable[[Any], Awaitable], loop=None):
    loop = loop or asyncio.get_running_loop()

    return ops.flat_map(
        lambda item: rx.from_future(
            loop.create_task(coro(item))
        )
    )


def through_subject(subject: rx.subject.Subject):
    """ Subject in the middle """
    def _through_subject(source):
        def subscribe(observer, scheduler=None):
            subject_dispose = source.subscribe(subject, scheduler=scheduler)
            return CompositeDisposable(subject_dispose, subject.subscribe(observer, scheduler=scheduler))

        return rx.create(subscribe)
    return _through_subject


def mobile_avg(window_count: int):
    def mobile_window(acc: list, item):
        acc.append(item)

        if len(acc) > window_count:
            acc.pop(0)

        return acc

    return rx.pipe(
        # collections.deque(), should be better for this purpose
        ops.scan(mobile_window, list()),
        ops.map(lambda item: sum(item) / len(item))
    )


""" BLOCK CLASSES """


class Http(Subject):
    def __init__(self, host: str = "localhost") -> None:
        super().__init__()
        self.loop = asyncio.get_running_loop()
        self.alock = asyncio.Lock()
        self.host = host
        self.subscribers_count = 0
        self.interval_get_path = None
        self.interval_get_period = None
        self.task = None

    def _subscribe_core(self, observer: typing.Observer,
                        scheduler: Optional[typing.Scheduler] = None) -> typing.Disposable:

        print(f"New subscription {self.subscribers_count}")

        if self.subscribers_count == 0 and self.interval_get_period is not None:
            self.task = self.loop.create_task(self.ainterval_get(self.interval_get_path, self.interval_get_period))

        self.subscribers_count += 1

        subscription = super()._subscribe_core(observer, scheduler)

        return CompositeDisposable(subscription, Disposable(lambda: self.dispose()))

    async def aget(self, path: str = '/'):
        log(f"http.get (host: {self.host}, path: {path}) [start]")

        delay = random.randint(1, 2)
        value = random.uniform(-6, 30)

        try:
            if path.find('heater_a') != -1:
                value = next(temp_a)
            elif path.find('heater_b') != -1:
                value = next(temp_b)
        except StopIteration:
            pass

        await asyncio.sleep(delay)

        # testing error catch and railway programming
        # raise NameError('HiThere')

        log(f"http.get (host: {self.host}, path: {path}, value: {value:.2f}, delay: {delay:.2f}) [end]")

        return value

    def interval_get(self, path: str = '/', period: float = 5):
        self.interval_get_path = path
        self.interval_get_period = period
        return self

    async def ainterval_get(self, path: str = '/', period: float = 5):
        while True and not self.is_disposed:
            async with self.alock:
                try:
                    value = await self.aget(path)
                except (Exception, asyncio.CancelledError) as ex:  # pylint: disable=broad-except
                    super().on_error(ex)
                else:
                    super().on_next(value)

            await asyncio.sleep(period)

    def dispose(self) -> None:
        self.subscribers_count -= 1

        if self.subscribers_count == 0:
            log("CLOSE CONNECTION!")
            # TODO: to try
            # self.task.cancel()
            self.loop.create_task(self.adispose())

    async def adispose(self) -> None:
        # Avoid dispose if ainterval_get running and can call on_next()
        async with self.alock:
            log("CLOSE CONNECTION! REAL")
            super().dispose()


class HttpV2:
    """ Encapsulate a ConnectableObservable """

    def __init__(self, host: str = "localhost") -> None:
        self._loop = asyncio.get_running_loop()
        self._host = host
        # ConnectableObservable
        self._observable = rx.create(self.on_subscribe).pipe(ops.share())
        self._observer = None
        self._scheduler = None

    def __call__(self, *args, **kwargs):
        return self._observable

    def on_subscribe(self, observer, scheduler):
        self._observer = observer
        self._scheduler = scheduler

        print("on_subscribe")
        observer.on_next("Sent at start of each new subscription?")

        # task = asyncio.get_event_loop().create_task(self._aio_sub())
        return Disposable(lambda: self.dispose())

    async def get(self, path: str = '/'):
        log(f"http.get (host: {self._host}, path: {path}) [start]")

        delay = random.randint(1, 2)
        value = random.uniform(-6, 30)

        await asyncio.sleep(delay)

        log(f"http.get (host: {self._host}, path: {path}) [end]")

        # Send to observers
        self._observer.on_next(value)

    def dispose(self) -> None:
        # close connection
        print("CLOSE CONNECTION!")


# PipedSubject
# TODO: check or implement dispose function
class AnalyzeAvg(Subject):
    def __init__(self, window_cont: int = 6, type='MOBILE_AVG') -> None:
        super().__init__()

        self._piped_subject = Subject()

        if type == 'MOBILE_AVG':
            avg_pipe = rx.pipe(mobile_avg(window_cont))
        else:
            avg_pipe = rx.pipe(
                ops.window_with_count(count=window_cont),
                ops.flat_map(lambda obs: obs.pipe(ops.average()))
            )

        self._piped_subject.pipe(
            avg_pipe
        ).subscribe(on_next=super().on_next, on_error=super().on_error, on_completed=super().on_completed)

    def on_next(self, value):
        self._piped_subject.on_next(value)


class PlanProportionalPower(Subject):

    def __init__(self, temp_target: float) -> None:
        super().__init__()
        self._temp_last = 0
        self._temp_target = temp_target

    @property
    def temp_target(self):
        return self._temp_target

    @temp_target.setter
    def temp_target(self, value):
        log(f"{__class__.__name__} set new temp_target: {value}")
        self._temp_target = value
        self.on_next(self._temp_last)

    def on_next(self, value) -> None:
        self._temp_last = value
        power = self.temp_target - value

        if power < 0:
            power = 0

        super().on_next(power)
