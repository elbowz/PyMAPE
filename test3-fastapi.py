import asyncio
import logging

import mape
from mape.loop import Loop
from mape.base_elements import Element
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
    loop = mape.Loop(uid='rest-test')

    @loop.execute
    def executer(item, on_next):
        # logger.debug(item)
        pass

    executer.debug(Element.Debug.IN)


    from mape.redis_remote import PostObservable

    # sub1 = PostObservable('/aq_bedroom/Monitor').subscribe(executer)
    # sub2 = PostObservable('/aq_bedroom/Monitor2').subscribe(executer)
    # # await asyncio.sleep(1)
    # print('dispose')
    #
    # print("ciao")
    # # sub1.dispose()
    # await asyncio.sleep(2)


if __name__ == '__main__':
    logger.debug('START...')

    mape.init(debug=True, redis_url='redis://localhost:6379', rest_host_port='0.0.0.0:6061')
    mape.run(entrypoint=async_main('test'))

    logger.debug('...STOP')
