from .rx_utils import (
    InfluxObserver,
    WriteOptions,
    Point
)

_config = {}


def set_config(config: dict):
    global _config
    _config = config






