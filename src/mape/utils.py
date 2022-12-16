import sys
import uuid
import inspect
import logging
import asyncio
import threading

import functools
from dataclasses import dataclass

_datefmt = '%H:%M:%S'
# _datefmt='%d %H:%M:%S'
_fmt = '%(asctime)s.%(msecs)-3d %(threadShortName)-3s %(name)-30s %(levelname)-8s %(message)s'
#_fmt = '%(relativeCreated)-6d %(threadShortName)-3s %(name)-20s: %(levelname)-8s %(message)s'


def cur_thread():
    """
    Return a unique number for the current thread'
    """
    n = threading.current_thread().name
    if 'Main' in n:
        return 'M'
    return '%s' % ('T' + n.rsplit('-', 1)[-1])


def log_record_enrich(record):
    record.threadShortName = cur_thread()
    return True


def init_logger(name: str = None, lvl: int = logging.WARNING, fmt: str = _fmt) -> logging.Logger:
    """
    Set base/root level logger for a package name

    Examples:
        ```python
        logger = init_logger()
        logger.info("Your message")
        ```

    Args:
        name: base logger name (ie. package name)
        lvl: log level
        fmt: format log string

    Returns:
        logger
    """
    formatter = logging.Formatter(fmt, datefmt=_datefmt)

    # Handler for stdout, filtered for log lvl lower than INFO
    h_out = logging.StreamHandler(sys.stdout)
    h_out.setLevel(logging.DEBUG)
    h_out.addFilter(lambda record: record.levelno <= logging.INFO)
    h_out.setFormatter(formatter)
    h_out.addFilter(log_record_enrich)

    # Handler for stderr, filtered for log lvl greater than WARNING
    h_err = logging.StreamHandler(sys.stderr)
    h_err.setLevel(logging.WARNING)
    h_err.setFormatter(formatter)
    h_err.addFilter(log_record_enrich)

    # Get (and mod) the base/root logger (eg. package name)
    logger = logging.getLogger(name)
    logger.setLevel(lvl)

    logger.addHandler(h_out)
    logger.addHandler(h_err)

    return logger


from rx.core import Observer


def caller_module_name(depth=1):
    # since we get this function caller
    depth += 1
    frame_info = inspect.stack()[depth]
    mod = inspect.getmodule(frame_info.frame)
    return mod.__name__ if mod else ''


class LogObserver(Observer):
    def __init__(self, postfix=None, module_name=None, enable=True):
        self.enable = enable
        self.prefix = f"({str(hash(self))[-4:]})"
        self.postfix = f" | {postfix}" if postfix else ''

        if module_name is None:
            # f.__globals__.get("_LOGGER", _LOGGER)
            self.logger = logging.getLogger(caller_module_name())
        else:
            self.logger = logging.getLogger(module_name)

        # If no logger is configured used standard print
        if not self.logger.hasHandlers():
            self.logger.info = print
            self.logger.error = print

    def on_next(self, value):
        self.enable and self.logger.info(f"{self.prefix} on next: {value}{self.postfix}")

    def on_error(self, error):
        self.enable and self.logger.error(f"on error: {error}{self.postfix}")

    def on_completed(self):
        self.enable and self.logger.info(f"completed{self.postfix}")


@dataclass
class GenericObject:
    pass


def generate_uid(collision_set=None, prefix=None):
    while True:
        uid = f"{prefix}{str(uuid.uuid4())[:8]}"
        if not collision_set or uid not in collision_set:
            break

    return uid


async def task_exception(awaitable, module_name=None):
    """
    Wrap coro() passed to asyncio.crete_task(), allow to catch exception during task execution
    note: https://bugs.python.org/issue39839

    Examples:
        >>> task = asyncio.create_task(task_exceptions(coro(*args, *kwargs))
        ...

    :param awaitable: coro() (coroutine object: an object returned by calling a coroutine function)
    :param module_name: name used for get logger
    :return: wrapped coro()
    """
    module_name = module_name or caller_module_name(5)
    logger = logging.getLogger(module_name)

    try:
        return await awaitable
    except Exception as e:
        logger.exception(e)


def log_task_exception(coro):
    """
    Decorator of task_exception(). Use on coro function instead of
    :param coro: coroutine function
    :return: wrapped coro()
    """
    module_name = caller_module_name()

    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        return await task_exception(coro(*args, **kwargs), module_name=module_name)
    return wrapped


def auto_task(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        awaitable = task_exception(func(*args, **kwargs))
        return asyncio.create_task(awaitable)
    else:
        return func(*args, **kwargs)


async def aio_call(func):
    """
    Call and return value independently func is a coro or classic func.
    note: of course must be used inside an async func.

    Examples:
        >>> await auto_call(func(args, kwargs))
        >>> await auto_call(coro(args, kwargs))
        ...
    """
    if inspect.iscoroutine(func):
        return await func
    else:
        return func


def setdefaultattr(obj, name, value):
    """ As Dict.setdefault but for object """
    try:
        return getattr(obj, name)
    except AttributeError:
        setattr(obj, name, value)
    return value
