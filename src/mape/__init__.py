from __future__ import annotations

import asyncio
import signal
import aioredis
import warnings
from asyncio import AbstractEventLoop
from fastapi import FastAPI
from typing import Dict

from rx.scheduler.eventloop import AsyncIOScheduler

from . import config as mape_config
from .application import App
from .base_elements import *
from .loop import Loop
# from .operators import *
from .remote.rest import UvicornDaemon, setup as rest_setup
from .remote.influxdb import set_config as set_influxdb
from .utils import init_logger, task_exception

# Please make sure the version here remains the same as in pyproject.toml
__version__ = "0.1.0a5"

# TODO: remove logger initialization
logger = logging.getLogger(__name__)
logging.getLogger(__name__).setLevel(logging.WARNING)
# Disable logging until user use logging.basicConfig()
# logger.addHandler(logging.NullHandler())

aio_loop: Optional[AbstractEventLoop] = None
rx_scheduler: Optional[AsyncIOScheduler] = None
redis: Optional[aioredis.Redis] = None
uvicorn_webserver: Optional[UvicornDaemon] = None
fastapi: Optional[FastAPI] = None
app: Optional[App] = None
config: Optional[Dict] = None


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
    uvicorn_webserver and uvicorn_webserver.stop()

    # Let's also cancel all running tasks:
    pending = asyncio.Task.all_tasks()

    for task in pending:
        logger.debug(f"Closing still running task: {task!r}")
        task.cancel()


def _start_web_server(host_port: str, loop):
    global uvicorn_webserver

    init_len_routes: Final = 4

    # Start Uvicorn webserver (forking a process) with the created routes by FastAPI
    if fastapi and (len_routes := len(fastapi.routes)) > init_len_routes:
        # The first 4 routes are instanced by default (ie swagger)
        from mape.remote.rest import UvicornDaemon

        host, port = host_port.split(':')
        uvicorn_webserver = UvicornDaemon(app=fastapi, loop=loop, host=host, port=port)

        system_path = fastapi.routes[:init_len_routes]
        mape_path = fastapi.routes[init_len_routes:]
        host_base_url = f"http://{uvicorn_webserver.config.host}:{uvicorn_webserver.config.port}"

        logger.info("APIs documentation:")
        for route in system_path:
            logger.info(f" * {host_base_url}{route.path}")

        logger.debug(f"Defined {len_routes - init_len_routes} REST MAPE endpoints:")
        for route in mape_path:
            logger.debug(f" * {host_base_url}{route.path}")

        logger.info('Webserver started: No more endpoint can be added since now!')


def init(debug: bool = False,
         asyncio_loop: AbstractEventLoop | None = None,
         redis_url: string | None = None,
         rest_host_port: string | None = None,
         config_file: string | None = None
         ) -> None:
    """Initialize the PyMAPE framework, internal variables and services.
    Allow configuration by passed arguments and/or `config_file`, giving priority on the first one.

    Call it before start using the framework.

    Examples:
        ```python
        mape.init(debug=True,
                redis_url="redis://localhost:6379",
                rest_host_port="0.0.0.0:6060",
                config_file="custom.yml")
        ```

    Args:
        debug: Enable more verbose mode.
        asyncio_loop: Provide your asyncio loop or leave PyMAPE to generate one for you.
        redis_url: Url of your Redis instance (eg. `redis://localhost:6379`)
        rest_host_port: Web server "host:port", where REST API endpoint will be provided (eg. `0.0.0.0:6060`).
        config_file: Path (absolute or relative to working directory) to the config file (default `mape.yml`).
    """
    global config, aio_loop, rx_scheduler, redis, fastapi, app

    if debug:
        # Configure a base (root module ) logger (StreamHandler, Formatter, etc...),
        # if user hasn't do one but enable debug
        logging.basicConfig(level=logging.DEBUG)
        # Set debug level also for PyMAPE
        logging.getLogger(__name__).setLevel(logging.DEBUG)

    config_file = config_file or mape_config.default_config_file

    if config := mape_config.load(config_file):
        logger.info(f"{config_file} loaded")
    else:
        logger.warning(f"{config_file} not found, using default config")
        config = mape_config.default

    mape_config.set('debug', debug)
    mape_config.set('redis.url', redis_url)
    mape_config.set('rest.host_port', rest_host_port)

    logger.debug(f"Config: {config}")

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

    if mape_config.get('redis.url'):
        redis = aioredis.from_url(redis_url, db=0)

    app = App(redis)

    if mape_config.get('rest.host_port'):
        fastapi = rest_setup(app, __version__)
        _start_web_server(rest_host_port, aio_loop)

    set_influxdb(mape_config.get('influxdb'))
    set_debug(mape_config.get('debug'))


def run(entrypoint: Union[Callable, Coroutine] = None):
    def on_done(_):
        # Catch stop execution (ie. ctrl+c or brutal stop)
        # notes: set the handler here to overwrite the Uvicorn handlers
        for signal_name in (signal.SIGINT, signal.SIGTERM):
            aio_loop.add_signal_handler(signal_name, stop)

        # loop.set_exception_handler(lambda *args: print("exception_handler", *args))

    if entrypoint is not None:
        if asyncio.iscoroutine(entrypoint):
            task = aio_loop.create_task(task_exception(entrypoint), name='entrypoint')
            task.add_done_callback(on_done)

    aio_loop.run_forever()


def set_debug(debug=False, asyncio_slow_callback_duration=0.1):
    # TODO: better debug and logging level support (it don't works as expected...)
    log_lvl = logging.DEBUG if debug else logging.WARNING

    # Enabling it, sometimes asyncio throw errors like:
    # "<_SelectorSocketTransport fd=11 read=polling write=<idle, bufsize=0>>: Fatal read error on socket transport"
    # aio_loop.set_debug(debug)

    debug and logging.getLogger(__name__).setLevel(log_lvl)
    logging.getLogger('asyncio').setLevel(log_lvl)

    if fastapi:
        fastapi.debug = debug
        # Avoid double logging for uvicorn
        logging.getLogger('uvicorn').handlers.clear()

    # Threshold for "slow" tasks.
    # Reduce to smaller value to throw the error and understand the behaviour.
    # The default is 0.1 (100 milliseconds).
    aio_loop.slow_callback_duration = asyncio_slow_callback_duration

    if debug:
        # Report all mistakes managing asynchronous resources.
        warnings.simplefilter('always', ResourceWarning)
    else:
        warnings.simplefilter('ignore', ResourceWarning)