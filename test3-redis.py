import asyncio
import logging

import mape
from mape.typing import Message, CallMethod
from mape.utils import LogObserver, init_logger

# Take the same mape package logger setup (eg. handler and format)
logger = init_logger('redis')
# ...alternative use you own logging prefernce
# logging.basicConfig(level=logging.WARNING, format='%(relativeCreated)6d %(name)s %(threadName)s %(message)s')
# logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

# mape lib debug
mape.setup_logger()
logging.getLogger('mape').setLevel(logging.DEBUG)


async def async_main(*args, **kwargs):

    loop = mape.Loop(uid='redis-test')

    @loop.execute
    def executer(item, on_next):
        logger.debug(item)

    from mape.redis_remote import SubObservable, subscribe_handler_deco, subscribe_handler

    @subscribe_handler_deco('__keyspace@*__:*', full_message=True, deserializer=lambda x: x)
    def keyspace(message):
        print("keyspace", message)

    await asyncio.sleep(6)
    keyspace.cancel()
    try:
        await keyspace.task
    except asyncio.CancelledError:
        print("after")

    sub = SubObservable(['aq_bedroom.Monitor', 'aq_kitchen.Monitor']).subscribe(executer)
    await asyncio.sleep(6)
    print('dispose')
    sub.dispose()

    @subscribe_handler_deco('aq_*.Monitor')
    def subscribed_func(message):
        print('message', message)

    await asyncio.sleep(6)
    subscribed_func.cancel()
    subscribed_func(666)
    print('cancel')

    class Test:
        def test(self, item):
            print("test", item)

    ciao = Test()
    task = subscribe_handler({'aq_*.Monitor': ciao.test})

    await asyncio.sleep(6)
    task.cancel()
    print('cancel')


if __name__ == '__main__':
    logger.debug('START...')

    mape.init(debug=True, redis_url='redis://localhost:6379')
    mape.run(entrypoint=async_main('test'))

    logger.debug('...STOP')
