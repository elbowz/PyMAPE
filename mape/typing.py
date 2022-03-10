from __future__ import annotations

from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple, TypeVar

from rx.core.typing import Observer

from mape import base_elements
from mape.utils import aio_call

T1 = TypeVar('T1')
T2 = TypeVar('T2')

OpsChain = Union[Tuple, Callable]
Mapper = Callable[[T1], T2]
DestMapper = Callable[[T1], Union[List[Observer], Observer]]


@dataclass
class Item:
    src: str = None
    dst: str = None
    # TODO: or list?!
    hops: int = 0
    timestamp: float = field(default_factory=lambda: datetime.timestamp(datetime.now()))

    @staticmethod
    def _element2path(element: Optional[base_elements.Element | str]):
        return element.path if hasattr(element, 'path') else element

    def add_hop(self, hop):
        # save history of hops?!
        # hop.path()
        self.hops += 1


@dataclass
class Message(Item):
    value: Any = None

    @classmethod
    def create(cls, value, *,
               src: Optional[base_elements.Element | str] = None,
               dst: Optional[base_elements.Element | str] = None):
        return cls(value=value, src=cls._element2path(src), dst=cls._element2path(dst))

    def __repr__(self):
        formatted_time = datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S.%f')[:-3]
        return f"{self.__class__.__name__}({self.value}, {self.src}, {self.dst}, {self.hops}, {formatted_time})"


@dataclass
class CallMethod(Item):
    name: str = None
    args: tuple | list = ()
    kwargs: dict = field(default_factory=lambda: dict())

    @classmethod
    def create(cls, name, *args, **kwargs):
        return cls(name=name, args=args, kwargs=kwargs)

    def exec(self, obj_or_module):
        # TODO: test with async Method (maybe something like): ElementFunc._on_next()
        return getattr(obj_or_module, self.name)(*self.args, **self.kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, {self.args}, {self.kwargs}, {self.src}, {self.dst}, {self.hops}, {self.timestamp})"


# TODO: delete... before check if somewhere is used
class MapeLoop(ABC):
    __slots__ = ()
    prefix: str = None

    @abstractmethod
    def __init__(self, uid: str = None, app=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_element(self, element):
        raise NotImplementedError

    @abstractmethod
    def has_element(self, element):
        raise NotImplementedError

    @abstractmethod
    def __contains__(self, element):
        raise NotImplementedError

    @abstractmethod
    def __getattr__(self, uid):
        """ Allow access (through dot notation) to mape elements.
        note: __getattr__() is called only when no real object attr exist. """
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, uid):
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError

    @abstractmethod
    def uid(self):
        raise NotImplementedError

    @abstractmethod
    def elements(self):
        raise NotImplementedError

    @abstractmethod
    def monitor(self, func=None, /, *,
                uid=None, ops_in: Optional[OpsChain] = (), ops_out: Optional[OpsChain] = ()
                ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def analyze(self, func=None, /, *,
                uid=None, ops_in: Optional[OpsChain] = (), ops_out: Optional[OpsChain] = ()
                ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def plan(self, func=None, /, *,
             uid=None, ops_in: Optional[OpsChain] = (), ops_out: Optional[OpsChain] = ()
             ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def execute(self,
                func=None,
                /, *,
                uid=None,
                ops_in: Optional[OpsChain] = (),
                ops_out: Optional[OpsChain] = ()
                ) -> Any:
        raise NotImplementedError
