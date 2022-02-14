from __future__ import annotations

import asyncio
import logging
import signal
import aioredis
import warnings
from contextlib import suppress
from fastapi import FastAPI

from typing import Any, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple
from rx.scheduler.eventloop import AsyncIOScheduler

import mape
from .application import App
from .base_elements import *
from .loop import Loop
# from .operators import *
from .remote.rest import UvicornDaemon, setup as rest_setup
from .utils import init_logger, task_exception

# Please make sure the version here remains the same as in project.cfg
__version__ = '0.0.1b'

# Disable logging until user use logging.basicConfig()
# TODO: remove logger inizialization
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

aio_loop: Optional[asyncio.AbstractEventLoop] = None
rx_scheduler: Optional[AsyncIOScheduler] = None
redis: Optional[aioredis.Redis] = None
uvicorn_webserver: Optional[UvicornDaemon] = None
fastapi: Optional[FastAPI] = None
# TODO: hosts_port is too ugly here
host_port: Optional[str] = None
app: Optional[App] = None


def setup_logger():
    """
    Helper for quickly adding a StreamHandler to the logger.
    Useful for debugging and lib debugging
    """
    # This method needs to be in this __init__.py to get the __name__ correct
    init_logger(__name__)

    # Stop propagation on upper logger_name (eg. __main__ and logging.basicConfig())
    logging.getLogger(__name__).propagate = False


def stop():
    aio_loop.stop()

    # Let's also cancel all running tasks:
    pending = asyncio.Task.all_tasks()

    for task in pending:
        logger.debug(f"Closing still running task: {task!r}")
        task.cancel()

    if uvicorn_webserver:
        uvicorn_webserver.stop()


def init(debug=False, asyncio_loop=None, redis_url=None, rest_host_port=None):
    global aio_loop, rx_scheduler, redis, fastapi, host_port, app

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

    # Catch stop execution (ie. ctrl+c or brutal stop)
    for signal_name in ('SIGINT', 'SIGTERM'):
        aio_loop.add_signal_handler(getattr(signal, signal_name), stop)

    # loop.set_exception_handler(lambda *args: print("exception_handler", *args))

    if redis_url:
        redis = aioredis.from_url(redis_url, db=0)

    app = App(redis)

    if rest_host_port:
        fastapi = rest_setup(app, __version__)
        host_port = rest_host_port

    set_debug(debug)


def run(entrypoint: Union[Callable, Coroutine] = None):
    def on_done(_):
        """ At the end of entrypoint all FastAPI path must be registered """
        global uvicorn_webserver

        init_len_routes: Final = 4

        # Start Uvicorn webserver (forking a process) with the created routes by FastAPI
        if fastapi and (len_routes := len(fastapi.routes) > init_len_routes):
            # The first 4 routes are instanced by default (ie swagger)
            from mape.remote.rest import UvicornDaemon

            host, port = host_port.split(':')
            uvicorn_webserver = UvicornDaemon(fastapi, host=host, port=port)
            uvicorn_webserver.start()

            system_path = fastapi.routes[:init_len_routes]
            mape_path = fastapi.routes[init_len_routes:]

            logger.debug(f"Defined {init_len_routes - len_routes} REST API endpoints")
            logger.debug(f"System endpoints and API documentation: {','.join([route.path for route in system_path])}")
            logger.debug(f"MAPE endpoints:")
            for route in mape_path:
                logger.debug(f" * {route.path}")

            logger.info('Webserver started: No more endpoint can be added since now!')

    if entrypoint is not None:
        if asyncio.iscoroutine(entrypoint):
            task = aio_loop.create_task(task_exception(entrypoint), name='entrypoint')
            task.add_done_callback(on_done)
        else:
            entrypoint()

    aio_loop.run_forever()


def set_debug(debug=False, asyncio_slow_callback_duration=0.1):
    log_lvl = logging.DEBUG if debug else logging.WARNING

    aio_loop.set_debug(debug)
    logging.getLogger(__name__).setLevel(log_lvl)
    logging.getLogger('asyncio').setLevel(log_lvl)

    if fastapi:
        fastapi.debug = debug

    # Threshold for "slow" tasks.
    # Reduce to smaller value to throw the error and understand the behaviour.
    # The default is 0.1 (100 milliseconds).
    aio_loop.slow_callback_duration = asyncio_slow_callback_duration

    if debug:
        # Report all mistakes managing asynchronous resources.
        warnings.simplefilter('always', ResourceWarning)
    else:
        warnings.simplefilter('ignore', ResourceWarning)
