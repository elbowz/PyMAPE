import random
from typing import Optional

import rx
import asyncio
import logging

from rx.core import typing

import mape
from mape import operators as mape_ops
from mape.base_elements import UID
from mape.typing import Message, CallMethod
from mape.utils import LogObserver, init_logger
from typing import Type, Any, List, Tuple, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple

# Take the same mape package logger setup (eg. handler and format)
logger = init_logger(__name__)
# ...alternative use you own logging prefernce
# logging.basicConfig(level=logging.WARNING, format='%(relativeCreated)6d ss %(name)s %(threadName)s %(message)s')
# logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

# mape lib debug
mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)

""" FIXITURES """


class VirtualRoom:
    def __init__(self, init_temperature: int, uid='Generic') -> None:
        self.heater_state = False
        self.uid = uid
        self._current_temperature = init_temperature

    def tick(self):
        import random
        tick_value = random.uniform(0, 1)

        if self.heater_state:
            self._current_temperature += tick_value
        else:
            self._current_temperature -= tick_value

    def set_heater(self, state: bool):
        logger.info(f"Set heater {self.uid} to {'ON' if state else 'OFF'}")
        self.heater_state = state

    @property
    def current_temperature(self):
        self.tick()
        return self._current_temperature


managed_element_room_a = VirtualRoom(20, 'A')
managed_element_room_b = VirtualRoom(16, 'B')

""" MAPE LOOPS AND ELEMENTS """

# LOOP HEATER A
heater_a = mape.Loop(uid='heater_a')


class HeaterMonitor(mape.base_elements.Monitor):

    async def _read_loop(self, interval=6):
        """ Simulate callback """
        while True and self.is_running:
            item = Message(value=managed_element_room_a.current_temperature, src=self.uid)
            self._on_next(item)
            managed_element_room_a.tick()
            await asyncio.sleep(random.randint(1, 10))

    def start(self, scheduler=None):
        disposable = super().start(scheduler=scheduler)

        # TODO: create a on_start() and wrap with asyncio.lock?!
        aioloop = mape.aio_loop or asyncio.get_event_loop()
        task = aioloop.create_task(self._read_loop(interval=6))

        return disposable

    def stop(self):
        super().stop()

    def test_call_method(self, args0, args1, kwargs0, kwargs1=None):
        print("real call to test_call_method", args0, args1, kwargs0, kwargs1)


@heater_a.plan(
    # 'plan' name is reserved in the MapeLoop class
    uid='heater_contact_plan',
    ops_in=mape_ops.debounce(5.0),
    # ops_out=mape_ops.do_action(lambda value: logger.info(f"ops_out decorator {value}")),
    )
def plan(item, on_next, self):
    item.value = True if item.value < self.target_temp else False
    on_next(item)


@heater_a.execute(uid=UID.DEF, ops_in=mape_ops.distinct_until_changed(lambda item: item.value))
def heater_execute(item, on_next, self):
    self.managed_element_room.set_heater(item.value)


# LOOP HEATER B
heater_b = mape.Loop(uid='heater_b')


@heater_b.monitor(uid=UID.DEF)
def monitor_b(item, on_next, self, something_useful=None):
    """ Simulate polling (ie read on call) """
    read_temperature = self.managed_element_room.current_temperature
    on_next(Message(value=read_temperature, src=self.uid))


class AnalyzeAVG(mape.base_elements.Analyze):
    def __init__(self, loop, window_count=6, uid: str = 'AnalyzeAVG', ) -> None:
        ops_out_avg = (
            mape_ops.window_with_count(count=window_count),
            mape_ops.flat_map(
                lambda obs: obs.pipe(
                    mape_ops.to_list(),
                    mape_ops.map(self._compute_avg_msg)
                )
            )
        )
        super().__init__(loop, uid, ops_out=ops_out_avg)

    def _compute_avg_msg(self, items):
        from functools import reduce
        items_sum = reduce(lambda acc, item: acc + item.value, items, 0)

        # Keep src and timestamp from first Message in items
        return Message(value=(items_sum / len(items)), src=items[0].src, timestamp=items[0].timestamp)


# Same name (heater_execute) used in heater_a...allowed like following var (re)assignement
@heater_b.execute(uid=UID.DEF, ops_in=mape_ops.distinct_until_changed())
def heater_execute(item, on_next, self):
    self.managed_element_room.set_heater(item.value)


# LOOP HEATER B
master = mape.Loop(uid='master')

start_time = asyncio.get_event_loop().time()


@master.analyze(uid='master_analyze')
def master_a(item, on_next, self):
    aioloop = mape.aio_loop or asyncio.get_event_loop()

    current_time = aioloop.time()
    if start_time + 10 <= current_time <= start_time + 20:
        print("TIME STOP", start_time, current_time)
        heater_a.heater_contact_plan.stop()
        heater_b.AnalyzeAVG.stop()
        item.value = False
        on_next(item)
    else:
        print("TIME START", start_time, current_time)
        heater_a.heater_contact_plan.start()
        heater_b.AnalyzeAVG.start()


# LOOP 4 TEST
test_loop = mape.Loop(uid='test')

from mape.base_elements import to_element_cls, to_monitor_cls, to_execute_cls


@test_loop.register
@to_execute_cls(
    # element_class=mape.base_elements.Plan,
    # default_uid=UID.DEF,
    default_ops_in=mape_ops.do_action(lambda item: print("in", item)),
    default_ops_out=mape_ops.do_action(lambda item: print("out", item)))
def my_to_element_class(item, on_next, self, something_useful=None):
    # print("my_to_element_class", item, on_next, self, something_useful)
    on_next(item)


@test_loop.add_func(
    # element_class=mape.base_elements.Plan,
    # default_uid=UID.DEF,
    ops_in=mape_ops.do_action(lambda item: print("in", item)),
    ops_out=mape_ops.do_action(lambda item: print("out", item)))
def my_func_register(item, on_next, self, something_useful=None):
    print("func_register", item, on_next, self, something_useful)
    on_next(item)


@test_loop.register
class MyClassTestRegister(mape.base_elements.Analyze):
    pass


@test_loop.execute(uid=UID.DEF, ops_in=mape_ops.distinct_until_changed())
def heater_execute_test(item, on_next, self):
    """ Docstring of heater_execute_test """
    self.managed_element_room.set_heater(item.value)


async def async_main(*args, **kwargs):
    logger.info(f"{'=' * 6} HEATER A {'=' * 6}")
    monitor = HeaterMonitor(loop=heater_a, uid='m_monitor')

    monitor.debug(mape.Element.Debug.IN)
    plan.debug(mape.Element.Debug.IN)
    heater_a.heater_execute.debug(mape.Element.Debug.IN)

    plan.target_temp = 20
    heater_a.heater_execute.managed_element_room = managed_element_room_a

    # monitor.pipe(
    #     mape_ops.through(plan),
    #     mape_ops.through(heater_a.heater_execute)
    # ).subscribe()

    # ... or
    monitor.subscribe(plan, scheduler=mape.rx_scheduler)
    plan.subscribe(heater_a.heater_execute, scheduler=mape.rx_scheduler)

    logger.info('TEST DEBOUNCE ON PLAN IN')
    plan.port_in.on_next(Message(value=22))
    plan.port_in.on_next(Message(value=22))
    plan.on_next(Message(value=22))
    plan.on_next(Message(value=22))
    print(type(plan._on_next), plan._on_next)
    print(type(monitor._on_next), monitor._on_next)
    await asyncio.sleep(6)

    logger.info('TEST DISTINCT ON HEATER_EXECUTE IN')
    heater_a.heater_execute.port_in.on_next(Message(value=True))
    heater_a.heater_execute.port_in.on_next(Message(value=True))
    heater_a.heater_execute.on_next(Message(value=True))
    heater_a.heater_execute.on_next(Message(value=True))
    await asyncio.sleep(1)

    monitor.start(scheduler=mape.rx_scheduler)

    logger.info('TEST CALLMETHOD ITEM')
    monitor.on_next(CallMethod(name='test_call_method', args=['args0', 'args1'], kwargs={'kwargs0': 'kwargs0'}))

    logger.info(f"{'=' * 6} HEATER B {'=' * 6}")

    monitor_b.debug(mape.Element.Debug.OUT)
    monitor_b.managed_element_room = managed_element_room_b
    monitor_b.start(scheduler=mape.rx_scheduler)

    analyze_avg = AnalyzeAVG(heater_b, 6)
    analyze_avg.debug(mape.Element.Debug.OUT)
    heater_b.heater_execute.managed_element_room = managed_element_room_b

    start = rx.timer(4.0, 2.0).pipe(
        mape_ops.map(lambda _: Message()),
        mape_ops.through(monitor_b),
        mape_ops.through(analyze_avg),
        mape_ops.map(lambda item: Message(value=item.value < 16)),
        mape_ops.through(heater_b.heater_execute)
    ).subscribe(scheduler=mape.rx_scheduler)

    # Direct call (force a read in this case)
    logger.info('TEST FORCE HEATER B READ (direct call to _on_next())')
    monitor_b(None, something_useful='something to pass')

    logger.info(f"{'=' * 6} MASTER LOOP {'=' * 6}")
    heater_a['m_monitor'].subscribe(master.master_analyze)
    heater_b.monitor_b.subscribe(master.master_analyze)
    master.master_analyze.subscribe(heater_a.heater_execute)
    master.master_analyze.subscribe(heater_b.heater_execute)
    master.master_analyze.start()

    for loop in mape.app:
        print("loop", loop.uid)
        for element in loop:
            print("element", element.uid)
    print("I'm full path", mape.app['heater_a.heater_contact_plan'])

    print(my_to_element_class, isinstance(my_to_element_class, mape.base_elements.Execute))
    my_to_element_class.on_next(Message(value=1))
    my_to_element_class(Message(value=3), something_useful='something to pass')
    print("--------------")
    print(mape.app.test.elements)
    print("--------------")
    print(isinstance(heater_execute_test, mape.base_elements.Execute))
    my_func_register.start()
    my_func_register.on_next(Message(value=2))
    help(heater_execute_test.__call__)


async def async_remote(*args, **kwargs):
    pass


if __name__ == '__main__':
    print('Main [start]')

    # ENABLE A PROMPT ON ASYNCIO
    # https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#prompt-in-an-asyncio-application
    # from prompt_toolkit import PromptSession
    # from prompt_toolkit.patch_stdout import patch_stdout
    #
    # async def my_coroutine():
    #     session = PromptSession()
    #     while True:
    #         with patch_stdout():
    #             result = await session.prompt_async('Say something: ')
    #
    #         print(mape.mape_loops['heater_a'].plan)
    #         mape.mape_loops['heater_a'].heater_contact.target_temp = 18
    #
    # loop = asyncio.get_event_loop()
    #
    # loop.create_task(my_coroutine())

    mape.init(True)
    # mape.run(entrypoint=async_main('test'))
    mape.run(entrypoint=async_remote())

    print('Main [end]')
