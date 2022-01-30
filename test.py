import asyncio
from collections import namedtuple

import rx
import rx.operators as ops
from rx.scheduler.eventloop import AsyncIOScheduler
from rx.subject import Subject

EchoItem = namedtuple('EchoItem', ['future', 'data'])


def test_tpc_server():
    def tcp_server(sink, loop):
        def on_subscribe(observer, scheduler):
            async def handle_echo(reader, writer):
                print("new client connected")
                while True:
                    data = await reader.readline()
                    data = data.decode("utf-8")
                    if not data:
                        break

                    future = asyncio.Future()
                    observer.on_next(EchoItem(
                        future=future,
                        data=data
                    ))
                    await future
                    writer.write(future.result().encode("utf-8"))

                print("Close the client socket")
                writer.close()

            def on_next(i):
                i.future.set_result(i.data)

            print("starting server")
            server = asyncio.start_server(handle_echo, '127.0.0.1', 8889)
            loop.create_task(server)

            sink.subscribe(
                on_next=on_next,
                on_error=observer.on_error,
                on_completed=observer.on_completed)

        return rx.create(on_subscribe)

    loop = asyncio.get_event_loop()
    proxy = Subject()
    source = tcp_server(proxy, loop)
    aio_scheduler = AsyncIOScheduler(loop=loop)

    source.pipe(
        ops.map(lambda i: i._replace(data="echo: {}".format(i.data))),
        ops.delay(1.0)
    ).subscribe(proxy)
    print("done")
    loop.run_forever()

    loop.close()


import time
import random
from datetime import timedelta
from typing import NamedTuple
from enum import Flag
from threading import current_thread

start = time.time()


def log(value: str):
    print(f"{time.time() - start:.3f} {current_thread().name} {value}")


# Fake HTTP_GET call (function with internal state...like a class)
def http_get(host: str = None):
    Payload = NamedTuple('Payload', [('value', float), ('delay', int)])

    async def _http_get(endpoint: str = '/'):
        log(f"http_get (host: {host} endpoint: {endpoint}) [start]")
        payload: Payload = Payload(value=random.uniform(-6, 30), delay=random.randint(1, 4))
        await asyncio.sleep(payload.delay)
        log(f"http_get (host: {host} endpoint: {endpoint}) [end]")
        return payload.value

    return _http_get


from asyncio import AbstractEventLoop


class TempAnalyze(rx.subject.Subject):
    #PlanRequest = Flag("PlanRequest", [('ANTI_FREEZE', 1), ('UP', 2), ('DOWN', 3)])
    ANTI_FREEZE: str = 'ANTI_FREEZE'
    UP: str = 'UP'
    DOWN: str = 'DOWN'

    def __init__(self, target_temp: float = 20, loop: AbstractEventLoop = None) -> None:
        super().__init__()
        self._loop = loop or asyncio.get_running_loop()
        self._target_temp = target_temp
        self._last_temp = 0

    @property
    def target_temp(self):
        return self._target_temp

    @target_temp.setter
    def target_temp(self, value):
        self._target_temp = value
        self._loop.create_task(self.find_symptoms(self._last_temp))

    async def find_symptoms(self, value):
        requests: set = set()

        if value < 0:
            requests.add(self.ANTI_FREEZE)

        if value < self.target_temp:
            requests.add(self.UP)
        else:
            requests.add(self.DOWN)

        super().on_next(requests)

    def on_next(self, value) -> None:
        self._last_temp = value
        self._loop.create_task(self.find_symptoms(value))

    def on_error(self, error: Exception) -> None:
        super().on_error(error)

    def on_completed(self) -> None:
        super().on_completed()


def heater_plan(value):
    if len({TempAnalyze.ANTI_FREEZE, TempAnalyze.UP} & value):
        return True

    if TempAnalyze.DOWN in value:
        return False

    return None


async def http_post(endpoint: str, value: str):
    log(f"http_post (endpoint: {endpoint}, {value}) [start]")
    await asyncio.sleep(random.randint(1, 4))
    log(f"http_post (endpoint: {endpoint}, {value}) [end]")
    return True

# maybe see publish()
class Analyze(rx.subject.Subject):

    def __init__(self) -> None:
        super().__init__()

    def fake_mqtt_subscribe(self, topic):
        log(f"subscribed to {topic}")
        asyncio.get_event_loop().create_task(self.loop_computation(topic))

    async def loop_computation(self, topic):
        while True:
            await asyncio.sleep(2)
            super().on_next(f"mqtt published ({topic}): {random.randint(1, 400)}")

    async def computation(self, value):
        log(f"analyzing {value}")
        time.sleep(4)
        # await asyncio.sleep(4)
        super().on_next(f"analyzed {value}")

    def on_next(self, value) -> None:
        asyncio.get_event_loop().create_task(self.computation(value))

    def on_error(self, error: Exception) -> None:
        super().on_error(error)

    def on_completed(self) -> None:
        super().on_completed()


from rx.disposable import Disposable
import functools


class FilteredSubject:
    def __init__(self):
        self._observer = None
        self._scheduler = None
        # ConnectableObservable
        self._observable = rx.create(self.on_subscribe).pipe(ops.share())

    def on_subscribe(self, observer, scheduler):

        print("on_subscribe")
        self._observer = observer
        self._scheduler = scheduler

        task = asyncio.get_event_loop().create_task(self._aio_sub())
        return Disposable(lambda: task.cancel())

    def get_observable(self):
        return self._observable

    def on_next(self, value):
        self._observer.on_next(value)

    async def _aio_sub(self):
        try:
            await asyncio.sleep(1)
            self._observer.on_next(random.randint(1, 400))
            await asyncio.sleep(1)
            self._observer.on_next(random.randint(1, 400))

            # loop.call_soon(
            #     observer.on_completed)
        except Exception as e:
            asyncio.get_event_loop().call_soon(
                functools.partial(self._observer.on_error, e))

# TRY ops.do() instead
def share_on_subject(subject: rx.subject.Subject):
    def _through_subject(source):
        def subscribe(observer, scheduler=None):
            def on_next(value):
                subject.on_next(value)
                observer.on_next(value)

            return source.subscribe(
                on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _through_subject


def through_subject(subject: rx.subject.Subject):
    def _through_subject(source):
        source.subscribe(subject)

        return subject

    return _through_subject


def simple_mapek():
    async def main(scheduler):
        loop = asyncio.get_running_loop()

        http_get_request = http_get("example.com")
        temp_analyze = TempAnalyze(20)

        # gather all termostat temperature
        temp_share = rx.subject.Subject()

        # calculate average temp of all thermostat each 4 reads
        temp_share.pipe(
            ops.window_with_count(count=4),
            ops.flat_map(lambda obs: obs.to(ops.average()))
        ).subscribe(lambda x: log(f"temp average {x} (each 4 read)"))

        polling_gap = timedelta(milliseconds=4000)
        polling = rx.interval(polling_gap, scheduler)

        # proxy_http_get_request = rx.subject.Subject()
        # proxy_http_get_request.subscribe(lambda x: log(f"proxy {x}"))

        polling.pipe(
            # MONITOR
            ops.flat_map(
                lambda _: rx.from_future(
                    loop.create_task(http_get_request("/path/to/temp"))
                )
            ),
            ops.do_action(lambda item: log(f"symptom/data: {item}")),

            share_on_subject(temp_share),

            # ANALYZER
            through_subject(temp_analyze),
            ops.do_action(lambda item: log(f"request adaptation: {item}")),

            # PLAN
            ops.map(heater_plan),
            ops.filter(lambda x: x is not None),
            ops.do_action(lambda item: log(f"request plan: {item}")),

            # EXECUTE
            ops.flat_map(
                lambda value: rx.from_future(
                    loop.create_task(http_post("/path/to/temp", value))
                )
            ),
        ).subscribe(lambda value: log(f"execute result: {value}"))

        """ Second thermostat with different polling, target temp, and pipe implementation """

        polling_gap_1 = timedelta(milliseconds=10000)
        polling_1 = rx.interval(polling_gap_1, scheduler)

        temp_analyze1 = TempAnalyze(16)

        polling_1.pipe(
            # MONITOR
            ops.flat_map(
                lambda _: rx.from_future(
                    loop.create_task(http_get_request("/path/to/temp 1"))
                )
            ),

            ops.do_action(lambda item: log(f"symptom/data 1: {item}")),
            share_on_subject(temp_share)
        ).subscribe(temp_analyze1)

        # ANALYZER
        temp_analyze1.pipe(
            ops.do_action(lambda item: log(f"request adaptation 1: {item}")),

            # PLAN
            ops.map(heater_plan),
            ops.filter(lambda x: x is not None),
            ops.do_action(lambda item: log(f"request plan 1: {item}")),

            # EXECUTE
            ops.flat_map(
                lambda value: rx.from_future(
                    loop.create_task(http_post("/path/to/temp 1", value))
                )
            ),
        ).subscribe(lambda value: log(f"execute result 1: {value}"))

        # change temp target for thermostat 1
        await asyncio.sleep(20)

        temp_analyze.target_temp = 6
        log("set new target temperature to 6")

        # temp_analyze.pipe(
        #     ops.do_action(lambda item: log(f"request adaptation: {item}"))
        # ).subscribe(lambda x: log(TempAnalyze.PlanRequest.ANTI_FREEZE in x))

        # TODO: add plan and execute

        log("main [end]")

    log("Pre-loop-run")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(True)

    import signal
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), loop.stop)

    scheduler = AsyncIOScheduler(loop)
    loop.create_task(main(scheduler))
    loop.run_forever()
    log("Post-loop-run")


def test_mapek():
    async def main(loop, scheduler):
        http_get_request = http_get("example.com")

        my_analyze = Analyze()

        polling_gap = timedelta(milliseconds=1000)
        polling = rx.interval(polling_gap, scheduler)

        log("Polling http_get_request")
        end = polling.pipe(
            ops.flat_map(lambda x: rx.from_future(
                loop.create_task(http_get_request("/path/to"))
            ))).subscribe(log)

        return

        print("- analyze")
        my_analyze.subscribe(
            on_next=lambda value: log(f"subscribe {value}"),
            # scheduler=scheduler
        )

        print("- analyze mod")
        my_analyze.to(
            # ops.subscribe_on(scheduler),
            ops.map(lambda x: f"forked {x}"), ops.do_action(print)).subscribe(
            # scheduler=scheduler
        )

        my_analyze.on_next("test")
        # await asyncio.sleep(6)
        my_analyze.on_next("test1")

        my_analyze_as_monitor = Analyze()

        print("- analyze as monitor")
        my_analyze_as_monitor.pipe(ops.map(lambda x: f"PUSH {x}"), ops.do_action(print)).subscribe(scheduler=scheduler)

        my_analyze_as_monitor.fake_mqtt_subscribe("test/topic")
        my_analyze_as_monitor.fake_mqtt_subscribe("test/topic2")

        filtered_subject = FilteredSubject()

        print("- filtered 1")
        filtered_subject.get_observable().pipe(
            ops.map(lambda x: f"1. FilteredSubject {x}"), ops.do_action(print)
        ).subscribe(scheduler=scheduler)

        print("- filtered 2")
        filtered_subject.get_observable().pipe(
            ops.map(lambda x: f"2. FilteredSubject {x}"), ops.do_action(print)
        ).subscribe(scheduler=scheduler)

        filtered_subject.on_next("Ciao")

    loop = asyncio.get_event_loop()
    aio_scheduler = AsyncIOScheduler(loop=loop)

    print("pre-loop")
    # loop.run_until_complete(loop.create_task(main(loop, aio_scheduler)))

    loop.create_task(main(loop, aio_scheduler))
    print("post-loop")
    loop.run_forever()


if __name__ == '__main__':
    # test_mapek()
    simple_mapek()
    # test_tpc_server()
