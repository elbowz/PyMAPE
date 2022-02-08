from __future__ import annotations

import asyncio
import logging
import aioredis
import warnings
from contextlib import suppress

from typing import Any, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple
from rx.scheduler.eventloop import AsyncIOScheduler

from .application import App
from .base_elements import *
from .loop import Loop
# from .operators import *
from .utils import init_logger

# Please make sure the version here remains the same as in project.cfg
__version__ = '0.0.1b'

# Disable logging until user use logging.basicConfig()
# TODO: remove logger inizialization
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

aio_loop: Optional[asyncio.AbstractEventLoop] = None
rx_scheduler: Optional[AsyncIOScheduler] = None
redis: Optional[aioredis.Redis] = None

app = App()


def setup_logger():
    """
    Helper for quickly adding a StreamHandler to the logger.
    Useful for debugging and lib debugging
    """
    # This method needs to be in this __init__.py to get the __name__ correct
    init_logger(__name__)

    # Stop propagation on upper logger_name (eg. __main__ and logging.basicConfig())
    logging.getLogger(__name__).propagate = False


def init(debug=False, asyncio_loop=None, redis_url=None):
    global aio_loop, rx_scheduler, redis

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop = asyncio_loop or loop or asyncio.get_event_loop()

    # TODO: check comment
    # We don't create a new event loop by default, because we want to be
    # sure that when this is called multiple times, each call of `init()`
    # goes through the same event loop. This way, users can schedule
    # background-tasks that keep running across multiple prompts.
    try:
        aio_loop = asyncio_loop or asyncio.get_event_loop()
    except RuntimeError:
        # Possibly we are not running in the main thread, where no event
        # loop is set by default. Or somebody called `asyncio.run()`
        # before, which closes the existing event loop. We can create a new
        # loop.
        aio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(aio_loop)

    rx_scheduler = rx_scheduler or AsyncIOScheduler(aio_loop)

    def on_stop():
        aio_loop.stop()

        # Let's also cancel all running tasks:
        pending = asyncio.Task.all_tasks()

        for task in pending:
            logger.debug(f"Closing still running task: {task!r}")
            task.cancel()


    import signal
    # Catch stop execution (ie. ctrl+c or brutal stop)
    for signame in ('SIGINT', 'SIGTERM'):
        aio_loop.add_signal_handler(getattr(signal, signame), on_stop)

    # loop.set_exception_handler(lambda *args: print("exception_handler", *args))

    if redis_url:
        redis = aioredis.from_url(redis_url, db=0)

    set_debug(debug)


def run(entrypoint: Union[Callable, Coroutine] = None):
    import inspect

    if entrypoint is not None:
        if inspect.iscoroutine(entrypoint):
            aio_loop.create_task(entrypoint, name='entrypoint')
        else:
            entrypoint()

    aio_loop.run_forever()


def set_debug(debug=False, asyncio_slow_callback_duration=0.1):
    log_lvl = logging.DEBUG if debug else logging.WARNING

    aio_loop.set_debug(debug)
    logging.getLogger(__name__).setLevel(log_lvl)
    logging.getLogger('asyncio').setLevel(log_lvl)

    # Threshold for "slow" tasks.
    # Reduce to smaller value to throw the error and understand the behaviour.
    # The default is 0.1 (100 milliseconds).
    aio_loop.slow_callback_duration = asyncio_slow_callback_duration

    if debug:
        # Report all mistakes managing asynchronous resources.
        warnings.simplefilter('always', ResourceWarning)
    else:
        warnings.simplefilter('ignore', ResourceWarning)
