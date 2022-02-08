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

    loop = mape.Loop(uid='redis')

    @loop.execute
    def executer(item, on_next):
        logger.debug(item)

    from mape.redis_remote import SubObservable
    SubObservable(['aq_bedroom.Monitor', 'aq_kitchen.Monitor']).subscribe(executer)

if __name__ == '__main__':
    logger.debug('START...')

    mape.init(debug=True, redis_url='redis://localhost:6379')
    mape.run(entrypoint=async_main('test'))

    logger.debug('...STOP')
