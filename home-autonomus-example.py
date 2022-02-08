import random
import asyncio

from datetime import timedelta
import rx
from rx.subject import Subject
from rx.scheduler.eventloop import AsyncIOScheduler

from lib import (
    log,
    ops,
    Http,
    HttpV2,
    map_async,
    through_subject,
    ShareMem,
    AnalyzeAvg,
    PlanProportionalPower
)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.set_debug(True)
rx_scheduler = AsyncIOScheduler(loop)

shared_mem = ShareMem()

import logging
import mape

from mape.utils import LogObserver, init_logger

init_logger(__name__)

logger = logging.getLogger(__name__)

async def main_a():
    logger.setLevel(logging.DEBUG)

    test = mape.BaseMapeElementTODELETE()

    test().on_next("before")
    a = test.subscribe(LogObserver("A"), scheduler=rx_scheduler)
    b = test.subscribe(LogObserver("B"), scheduler=rx_scheduler)
    c = test.subscribe(LogObserver("C"), scheduler=rx_scheduler)
    test().on_next("ciao")

    await asyncio.sleep(1)

    test().on_next("ciao2")

    a.dispose()
    b.dispose()
    test.port().on_next("ciao3")
    c.dispose()

    test().on_next("ciao4")

    test.stop()

    test().on_next("ciao5")

    d = test.subscribe(LogObserver("D"), scheduler=rx_scheduler)
    test.start()

    test().on_next("ciao6")


async def main():
    coro_func = [
        heater_a_mape_loop(),
        heater_b_mape_loop()
    ]

    log("> START HEATERS")
    await heater_b_mape_loop()
    # await asyncio.gather(*coro_func)

    log("> START CONTROLLER")
    # await heaters_controller()


async def heaters_controller():

    # gather all termostat temperature
    temp_share = rx.subject.Subject()
    hasattr(shared_mem, 'heater_a_monitor') and shared_mem.heater_a_monitor.subscribe(temp_share)
    hasattr(shared_mem, 'heater_b_monitor') and shared_mem.heater_b_monitor.subscribe(temp_share)

    # calculate average temp of all thermostat each 4 reads
    temp_share.pipe(
        ops.window_with_count(count=4),
        ops.flat_map(lambda obs: obs.to(ops.average()))
    ).subscribe(lambda item: log(f"CONTROLLER: Temp average of all room {item:.2f} (each 4 read)"), scheduler=rx_scheduler)

    await asyncio.sleep(16)

    if hasattr(shared_mem, 'heater_a_temp_target'):
        log(f"CONTROLLER: Set HEATER A temp target")
        shared_mem.heater_a_temp_target = 4

    await asyncio.sleep(20)

    if hasattr(shared_mem, 'plan_prop_power'):
        log(f"CONTROLLER: Set HEATER B temp target")
        shared_mem.plan_prop_power.temp_target = 8

    await asyncio.sleep(4)

    if hasattr(shared_mem, 'heater_a_execute'):
        log('CONTROLLER: Force (until next loop) switch on HEATER A')
        shared_mem.heater_a_execute.on_next(True)


async def heater_a_mape_loop():
    """ POLLING WITH INTERVAL ON ASYNC FUNC """
    log("HEATER A: temp_target 22")
    shared_mem.setdefault('heater_a_temp_target', 22)

    monitor_heater = Http('heater_a.com')

    monitor = Subject()
    shared_mem.heater_a_monitor = monitor
    execute = Subject()
    shared_mem.heater_a_execute = execute

    from lib import VirtualRoom
    virtual_room = VirtualRoom(16)

    # Set polling interval
    # period = timedelta(milliseconds=2000)
    # datetime for absolute date (eg. chrono thermostat)
    a = rx.timer(0, 2.0).pipe(

        # MONITOR (virtual room)
        ops.map(lambda _: virtual_room.current_temperature),
        ops.do_action(lambda item: log(f"HEATER A: {item:.2f} (temperature)")),
        ops.do_action(lambda _: virtual_room.tick()),

        # MONITOR (polling data in async way from monitor_heater used like a simple function)
        # map_async(lambda _: monitor_heater.aget('/path/to/heater_a')),
        # Fork on a subject, allowing eventually observers to subscribe (from this point)
        ops.do(monitor),

        # ANALYZE/PLAN (?!)
        ops.map(lambda item: item < shared_mem.heater_a_temp_target),
        # Pass item through the subject (ie we can do execute.on_next())
        through_subject(execute),

        # EXECUTE
        # Remove consecutive duplicate
        ops.distinct_until_changed(lambda item: item),
        # or ...
        # ops.group_by(lambda item: item),
        # ops.flat_map(lambda obs: obs.pipe(ops.first())),

        # Switch on/off heater
        ops.do_action(lambda item: virtual_room.set_heater(item)),
        ops.do_action(lambda item: log(f"HEATER A: {item} (state)")),
    ).subscribe(scheduler=rx_scheduler)

    # await asyncio.sleep(5)
    #
    # a.dispose()


async def heater_b_mape_loop():
    """ POLLING DIRECTLY IN CLASS """
    monitor_heater = Http('heater_b.com')
    monitor_heater.interval_get('/path/to/heater_b', 4.0)
    shared_mem.heater_b_monitor = monitor_heater

    log("HEATER B: avg 4, temp_target 26")
    analyze_avg = AnalyzeAvg(4, 'AVG')
    # analyze_avg = AnalyzeAvg(4, 'MOBILE_AVG')
    plan_prop_power = PlanProportionalPower(26)
    shared_mem.plan_prop_power = plan_prop_power

    a = monitor_heater.pipe(
        # Glue code (ie reactiveX operators)
    ).subscribe(analyze_avg, scheduler=rx_scheduler)

    b = analyze_avg.pipe(
        # Glue code (ie reactiveX operators)
        ops.do_action(lambda item: log(f"HEATER B: {item:.2f} (average temp)"))
    ).subscribe(plan_prop_power, scheduler=rx_scheduler)

    c = plan_prop_power.pipe(
        # Glue code (ie reactiveX operators)
        ops.do_action(lambda item: log(f"HEATER B: {item:.2f} (proportional power)"))
    ).subscribe(scheduler=rx_scheduler)

    # await asyncio.sleep(30)
    #
    # a.dispose()


if __name__ == '__main__':
    log('Main [start]')

    import signal

    # Catch stop execution (ie. ctrl+c or brutal stop)
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), loop.stop)

    #loop.create_task(main())
    loop.create_task(main())

    log('Main [end]')

    loop.run_forever()
