from .rx_utils import (
    InfluxObserver,
    SYNCHRONOUS,
    ASYNCHRONOUS,
    Point
)

_config = {}


def set_config(config: dict):
    global _config
    _config = config






