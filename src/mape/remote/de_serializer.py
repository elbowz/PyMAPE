from __future__ import annotations

import json
import pickle
from typing import Type, Any, List

from purse.collections import T
from pydantic import BaseModel


class Pickled:
    pass


def obj_from_raw(value_type: Type[T], raw_item: str | bytes) -> T | Any:
    if issubclass(value_type, BaseModel):
        return value_type.parse_raw(raw_item)
    elif issubclass(value_type, Pickled):
        return pickle.loads(raw_item)
    elif issubclass(value_type, dict):
        return json.loads(raw_item)
    elif issubclass(value_type, str):
        if isinstance(raw_item, bytes):
            return raw_item.decode()
        else:
            return raw_item
    else:
        if isinstance(raw_item, str):
            return raw_item.encode()
        else:
            return raw_item


def list_from_raw(value_type: Type[T], raw_list: List[Any]) -> List[T]:
    obj_list: List[T] = []
    if issubclass(value_type, BaseModel):
        for raw_item in raw_list:
            obj: Any = value_type.parse_raw(raw_item)
            obj_list.append(obj)
        return obj_list
    elif issubclass(value_type, Pickled):
        for raw_item in raw_list:
            obj: Any = pickle.loads(raw_item)
            obj_list.append(obj)
    elif issubclass(value_type, dict):
        for raw_item in raw_list:
            obj = json.loads(raw_item)
            obj_list.append(obj)
        return obj_list
    elif issubclass(value_type, str):
        for raw_item in raw_list:
            if isinstance(raw_item, bytes):
                obj = raw_item.decode()
                obj_list.append(obj)
            else:
                obj_list.append(raw_item)
        return obj_list
    else:
        for raw_item in raw_list:
            if isinstance(raw_item, str):
                obj = raw_item.encode()
                obj_list.append(obj)
            else:
                obj_list.append(raw_item)
        return obj_list


def obj_to_raw(value_type: Type[T], value: T) -> str | bytes:
    if isinstance(value, BaseModel) and isinstance(value, value_type):
        assert isinstance(value, BaseModel)
        return value.json()
    elif value_type is Pickled:
        return pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
    elif isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, (str, bytes)):
        return value
    else:
        raise ValueError(
            f"Incorrect type. Expected type: {value_type} "
            f"while give Value type {type(value)}")
