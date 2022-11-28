from __future__ import annotations

from aioredis import Redis
from typing import Any, Dict, Type, Union, Tuple, Iterable, List, TypeVar

from mape.loop import Loop
from mape.base_elements import Element
from mape.level import Level
from mape.knowledge import Knowledge
from mape.utils import generate_uid
from mape.constants import RESERVED_PREPEND, RESERVED_SEPARATOR


class App:
    uid: str = 'app'

    def __init__(self, redis: Redis) -> None:
        self._redis: Redis = redis
        self._loops: Dict[str, Loop] = dict()
        self._levels: Dict[str, Level] = dict()
        self._k = Knowledge(self._redis, f"k{RESERVED_SEPARATOR}{self.uid}")

    def add_loop(self, loop):
        uid = loop.uid or generate_uid(self._loops, prefix=loop.prefix)

        if self.has_loop(uid) or hasattr(self, uid):
            return False

        loop._uid = uid
        loop._app = self
        self._loops[uid] = loop

        return uid

    register = add_loop

    def has_loop(self, loop) -> bool:
        uid = loop.uid if hasattr(loop, 'uid') else loop
        return uid in self._loops

    def __contains__(self, loop):
        return self.has_loop(loop)

    def __getattr__(self, uid):
        """ Allow access (through dot notation) to mape loops.
        note: __getattr__() is called only when no real object attr exist. """
        if uid in self._loops:
            return self._loops[uid]

        super().__getattribute__(uid)

    def __getitem__(self, path: str) -> Loop | Element | Level:
        items = path.split(RESERVED_SEPARATOR)
        count_items = len(items)

        if count_items == 1:
            # path: 'loop_uid'
            try:
                return self._loops[items[0]]
            except KeyError as err:
                raise KeyError(f"Loop '{items[0]}' not exist")
        elif count_items == 2:
            # path: 'loop_uid.element_uid'
            loop = self[items[0]]
            return loop[items[1]]
        elif count_items == 3:
            # path: 'level_uid.loop_uid.element_uid'
            try:
                level = self._levels[items[0]]
            except KeyError as err:
                raise KeyError(f"Level '{items[0]}' not exist")
            return level[items[1]]

        raise KeyError(f"Path is malformed {path}")

    def __iter__(self):
        return iter(self._loops.values())

    def add_default_level(self, level_uid: str):
        """
        Create and add the new level only if not already exist
        ie. no conflict management like loop, if already exist return that
        """
        if level_uid not in self._levels:
            self._levels[level_uid] = Level(level_uid, app=self)

        return self._levels[level_uid]

    @property
    def redis(self):
        return self._redis

    @property
    def loops(self):
        return self._loops

    @property
    def levels(self):
        return self._levels

    @property
    def k(self) -> Knowledge:
        return self._k
