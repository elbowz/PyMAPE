from typing import Any, Callable

import rx
import asyncio
import logging

from rx import operators as ops

import mape
from mape import operators as mape_ops
from mape.utils import LogObserver, init_logger

# Take the same mape package logger setup (eg. handler and format)
init_logger(__name__)
# ...alternative use you own logging prefernce
# logging.basicConfig(level=logging.WARNING, format='%(relativeCreated)6d ss %(name)s %(threadName)s %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


heater_a = mape.Loop(uid='heater-a')
heater_b = mape.Loop(uid='heater-b')
print("loops", mape.mape_loops)


@heater_a.monitor
def my_monitor(value, move_on, ciao="casaA"):
    print("my_monitor executed", value, move_on, ciao)
    move_on(value)
    move_on(value + 1)


@heater_b.monitor(ciao=True)
def my_monitor_B(value, move_on, ciao="casaB"):
    print(value, move_on, ciao)
    pass


class VirtualRoom:
    def __init__(self, init_temperature: int) -> None:
        self.heater_state = False
        self.current_temperature = init_temperature

    def tick(self):
        import random
        tick_value = random.uniform(0, 1)

        if self.heater_state:
            self.current_temperature += tick_value
        else:
            self.current_temperature -= tick_value

    def set_heater(self, state: bool):
        self.heater_state = state
        self.tick()


managed_element_room = VirtualRoom(20)


class HeaterMonitor(mape.Monitor):

    async def _read_loop(self, interval=6):
        while True and self.is_running:
            # TODO: Uncomment _on_next() and use that
            self._p_out.input.on_next(managed_element_room.current_temperature)
            await asyncio.sleep(6)

    def start(self):
        disposable = super().start()

        # TODO: create a on_start() and wrap with asyncio.lock?!
        aioloop = asyncio.get_event_loop()
        task = aioloop.create_task(self._read_loop(interval=6))

        return disposable

    def stop(self):
        super().stop()


@heater_a.plan
def plan(value, move_on, ciao="casaA"):
    value = True if value < 20 else False
    move_on(value)


@heater_a.execute
def heater_execute(value, move_on, ciao="casaA"):
    managed_element_room.set_heater(value)


async def async_main(test):
    logger.info(f"{'='*6} ASYNC MAIN {'='*6}")

    monitor = HeaterMonitor(uid='monitor')
    heater_a.add_element(monitor)

    monitor.debug(mape.Element.Debug.IN | mape.Element.Debug.OUT)
    plan.debug(mape.Element.Debug.IN | mape.Element.Debug.OUT)
    heater_execute.debug(mape.Element.Debug.IN)

    monitor.pipe(
        mape_ops.through(plan),
        mape_ops.through(heater_a.heater_execute)
    ).subscribe()

    monitor.start()

    await asyncio.sleep(10)
    print("ciao")
    plan.stop()
    monitor.stop()
    heater_execute.on_next(True)
    heater_execute.on_next(False)

    # monitor.subscribe()
    return

    my_monitor.subscribe(my_analyze)
    my_monitor.start()
    my_analyze.subscribe(LogObserver("ANALYZE"))
    my_monitor(5)
    print('elements', heater_a.my_monitor, heater_a['analyze666'])
    print("qui", my_monitor_B in heater_a)
    for element in heater_a:
        print(element)
    return

    test4decorator = Test4Decorator(uid="no_collision666")
    my_loopA.add_element(test4decorator)

    analyze = mape.StartOnSubscribe(uid="cazzi miei")
    analyze.debug(mape.Element.Debug.IN | mape.Element.Debug.OUT)
    analyze.on_next(6)
    analyze.subscribe()
    return

    print("loop", my_loopA.no_collision666)
    my_monitor.subscribe(test4decorator)
    test4decorator.start()
    test4decorator.subscribe(LogObserver('decorator class monitor'))
    my_monitor.start()
    my_monitor.debug(mape.Element.Debug.IN | mape.Element.Debug.OUT)
    my_monitor.on_next(666)
    my_monitor(777, ciao="okkkk")
    print(my_monitor.loop.elements)
    return

    monitor = mape.Element(None)
    analyze = mape.StartOnSubscribe()

    monitor.pipe(
        mape.through(analyze)
    ).subscribe(LogObserver("LOOP"))

    monitor.p_in.subscribe(LogObserver("monitor source"))
    monitor.p_out.subscribe(LogObserver("monitor sink"))
    analyze.p_out.subscribe(LogObserver("monitor sink"))
    monitor.on_next("before start")
    analyze.on_next("on analyze")
    dispose = monitor.start()
    monitor.on_next("after start")
    dispose.dispose()
    # monitor.stop()
    monitor.on_next("after stop")
    monitor.start()
    monitor.on_next("after start2")

    logger.info(f"{'='*6} ASYNC MAIN 2 {'='*6}")

    monitor = mape.Element(None)
    analyze = mape.StartOnSubscribe()

    monitor.subscribe(analyze)
    monitor.start()
    monitor.on_next(666)

    return
    test.on_next("before")
    a = test.to().subscribe(LogObserver("A"))
    test.on_next("missed")
    b = test.subscribe(LogObserver("B"))

    test.on_next("1")
    a.dispose()
    test.dispose()
    test.on_next("2")
    b.dispose()

    test.p_in.subscribe(LogObserver("sub on source"))
    test.sink.subscribe(LogObserver("sub on sink"))
    test.subscribe(LogObserver("after dispose"))

    test.on_next("push 4")
    test.p_in.on_next("push 4 on source")
    test.sink.on_next("push 4 on sink")
    return

    print("dopo")
    test.on_next("ciao")

    await asyncio.sleep(1)

    test.on_next("ciao2")

    a.dispose()
    b.dispose()
    test.on_next("ciao3")
    test.p_in.on_next("ciao4 on source")
    test.sink.on_next("ciao4 on sink")

    test.p_in.subscribe(LogObserver("on source"))
    test.sink.subscribe(LogObserver("on sink"))
    test.on_next("ciao 4 test source-sink sub")
    c.dispose()

    # test.stop()

    test.on_next("ciao5")

    d = test.subscribe(LogObserver("D"))
    # test.start()

    test.on_next("ciao6")
    test.on_next("ciao7")


def main(test):
    logger.info(f"{'='*6} MAIN {'='*6}")


if __name__ == '__main__':
    print('Main [start]')

    # import functools
    mape.init(True, entrypoint=async_main("test"))

    # ... or
    # mape.init(True)
    # mape.loop.create_task(async_main("test"))
    # print('Main [end]')
    # mape.loop.run_forever()
