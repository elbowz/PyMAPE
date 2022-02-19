import random
import asyncio
import logging

import mape
from mape.typing import Message, CallMethod
from mape.utils import LogObserver, init_logger

# Take the same mape package logger setup (eg. handler and format)
logger = init_logger()
# ...alternative use you own logging prefernce
# logging.basicConfig(level=logging.WARNING, format='%(relativeCreated)6d %(name)s %(threadName)s %(message)s')
# logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

# mape lib debug
mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


async def async_main(*args, **kwargs):
    from loops.fixtures import VirtualRoom
    from loops import thermostats, air_quality, alarm

    # Managed elements
    kitchen = VirtualRoom(init_temperature=20, init_air_quality=36, uid='kitchen')
    bedroom = VirtualRoom(init_temperature=14, init_air_quality=42, uid='bedroom')
    # bathroom = VirtualRoom(init_temperature=24, init_air_quality=36, uid='bathroom')

    # Init loops thermostat
    l_kitchen = thermostats.make(f"th_{kitchen.uid}", target_temp=20, room=kitchen)
    l_bedroom = thermostats.make(f"th_{bedroom.uid}", target_temp=16, room=bedroom)
    # l_bathroom = thermostats.make(f"th_{bathroom.uid}", target_temp=16, room=bathroom)

    # List loops init
    logger.debug(f"LOOPS: {list(mape.app.loops.keys())}")

    # Iterate over loops and element
    for loop in mape.app:
        logger.debug(f"* {loop.uid}")
        for element in loop:
            logger.debug(f" - {element.uid}")

    # Access to loop/element
    p = mape.app['th_kitchen.plan4th_kitchen']
    logger.debug(f"access by key/path string app['th_kitchen.plan4th_kitchen']: {p.uid}")
    uid = mape.app.th_kitchen.Monitor.uid
    logger.debug(f"access by dot notation app.th_kitchen.Monitor: {uid}")

    logger.debug(f"{'=' * 6} Debounce test on Plan plan4thermostat {'=' * 6}")
    p.port_in.on_next(22)
    mape.app.th_kitchen.plan4th_kitchen.port_in.on_next(21)
    # default on_next() is on port_in
    l_kitchen.plan4th_kitchen.on_next(20)
    l_kitchen.plan4th_kitchen.on_next(23)

    logger.debug('Sleeping for 6 seconds...')
    await asyncio.sleep(6)

    logger.debug(f"{'=' * 6} Distinct test on Execute {'=' * 6}")
    # Retrive execute element from kitchen loop by type, because uid is random
    e_kitchen = [element for element in l_kitchen if isinstance(element, mape.base_elements.Execute)][0]

    e_kitchen.on_next(True)
    # Allow the e_kitchen func (coro in a task) to execute
    await asyncio.sleep(0)
    e_kitchen.on_next(True)
    e_kitchen.on_next(True)
    e_kitchen.on_next(True)

    logger.debug('Sleeping for 1 second...')
    await asyncio.sleep(1)

    logger.debug(f"{'=' * 6} Element ({e_kitchen.uid}) direct call of function {'=' * 6}")
    # Ignore the ops_in (ie. distinct)
    # Autodetect coroutine function (decide if you want await or not
    await e_kitchen(True, useful_params='something')

    logger.debug(f"{'=' * 6} Element ({l_kitchen.Monitor.uid}) call of method using item {'=' * 6}")
    # Start and stop to allow receiving CallMethod item
    l_kitchen.Monitor.start()
    l_kitchen.Monitor.on_next(CallMethod.create('test_call_method', args=['A', 'B'], kwargs={'kwargs0': 'C'}))
    l_kitchen.Monitor.stop()

    logger.debug('Sleeping for 1 second...')
    await asyncio.sleep(1)

    # Start monitor elements
    l_kitchen.Monitor.start()
    l_bedroom.Monitor.start()
    # l_bathroom.Monitor.start()

    # Init loops air quality
    l_kitchen = air_quality.make(f"aq_{kitchen.uid}", room=kitchen)
    l_bedroom = air_quality.make(f"aq_{bedroom.uid}", room=bedroom)
    # l_bathroom = air_quality.make(f"aq_{bathroom.uid}", room=bathroom)

    l_kitchen.Monitor.start()
    l_bedroom.Monitor.start()
    # l_bathroom.Monitor.start()

    # Connect all Monitor in air quality loop to alarm loop (AVG)
    alarm.make()

    # List of live loops and levels
    logger.debug(f"LOOPS: {(mape.app.loops.keys())}")
    logger.debug(f"LEVELS: {(mape.app.levels.keys())}")

    # Iterate over level, loop, element
    for level in mape.app.levels.values():
        logger.debug(f"* {level.uid}")
        for loop in level:
            logger.debug(f" - {loop.uid}")
            for element in loop:
                logger.debug(f"  > {element.uid}")

    # Access to loop/element
    a = mape.app['1.aq_master.a_avg']
    logger.debug(f"access by key/path string app['B.aq_master.a_avg']: {a.uid}")
    uid = mape.app.levels['0'].aq_kitchen.Monitor.uid
    logger.debug(f"access by dot notation mape.app.levels['A'].aq_kitchen.Monitor.uid: {uid}")

if __name__ == '__main__':
    logger.debug('START...')

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

    mape.init(debug=True, redis_url='redis://localhost:6379', rest_host_port='0.0.0.0:6060')
    mape.run(entrypoint=async_main('test'))

    logger.debug('...STOP')
