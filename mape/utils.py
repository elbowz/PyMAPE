import sys
import uuid
import inspect
import logging
import threading

from typing import Any
from dataclasses import dataclass

from .typing import CallMethod

_datefmt = '%H:%M:%S'
# _datefmt='%d %H:%M:%S'
_fmt = '%(asctime)s.%(msecs)d %(threadShortName)-3s %(name)-20s: %(levelname)-8s %(message)s'
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
    :param name: base logger name (ie. package name)
    :param lvl: default log level
    :param fmt: format log string
    :return: logger
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
    def __init__(self, postfix=None, module_name=None):
        self.prefix = f"({str(hash(self))[-4:]})"
        self.postfix = f" | {postfix}" if postfix else ''

        if module_name is None:
            # f.__globals__.get("_LOGGER", _LOGGER)
            self.logger = logging.getLogger(caller_module_name())
        else:
            self.logger = logging.getLogger(module_name)

        if not self.logger.hasHandlers():
            self.logger.info = print
            self.logger.error = print

    def on_next(self, value):
        self.logger.info(f"{self.prefix} on next: {value}{self.postfix}")

    def on_error(self, error):
        self.logger.error(f"on error: {error}{self.postfix}")

    def on_completed(self):
        self.logger.info(f"completed{self.postfix}")


@dataclass
class GenericObject:
    pass


def generate_uid(collision_set=None, prefix=None):
    while True:
        uid = f"{prefix}{str(uuid.uuid4())[:8]}"
        if not collision_set or uid not in collision_set:
            break

    return uid
