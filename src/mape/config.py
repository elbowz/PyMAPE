import os
import yaml
from functools import reduce
from typing import Dict, Any

default_config_file = 'mape.yml'
config_dict = {}


def set_config(config: Dict):
    global config_dict
    config_dict = config


def load(file: str = None):
    try:
        file = file or default_config_file
        with open(file, 'r') as config_file:
            config = yaml.load(config_file, Loader=yaml.Loader)
            set_config(config)
            return config
    except FileNotFoundError as e:
        return False


def get(path: str, default: Any = None, cfg: Dict = None):
    keys = path.split('.')
    cfg = cfg or config_dict

    ret = reduce(lambda c, k: c.get(k, {}), keys, cfg)
    return default if isinstance(ret, Dict) and not len(ret) else ret


def set(path: str, value, cfg = None):
    if value is None:
        return None

    keys = path.split('.')
    cfg = cfg or config_dict

    for key in keys[:-1]:
        cfg = cfg.setdefault(key, {})

    cfg[keys[-1]] = value
    return value


# Load from mape lib directory
default = load(os.path.dirname(os.path.realpath(__file__)) + '/mape.default.yml')
set_config(default)
