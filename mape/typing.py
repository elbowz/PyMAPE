from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Type, Any, List, Tuple, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple, TypeVar

from rx.core.typing import Observer

T1 = TypeVar('T1')
T2 = TypeVar('T2')

OpsChain = Union[Tuple, Callable]
Mapper = Callable[[T1], T2]
DestMapper = Callable[[T1], Observer]


@dataclass
class Item:
    src: str = None
    dst: str = None
    hops: int = 0
    timestamp: float = field(default_factory=lambda: datetime.timestamp(datetime.now()))


@dataclass
class Message(Item):
    value: Any = None

    def __repr__(self):
        formatted_time = datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S.%f')[:-3]
        return f"{self.__class__.__name__}({self.value}, {self.src}, {self.dst}, {self.hops}, {formatted_time})"


@dataclass
class CallMethod(Item):
    name: str = None
    args: list = None
    kwargs: dict = None

    def exec(self, obj_or_module):
        return getattr(obj_or_module, self.name)(*self.args, **self.kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, {self.args}, {self.kwargs}, {self.src}, {self.dst}, {self.hops}, {self.timestamp})"


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
                uid=None, ops_in: Optional[OpsChain] = (), ops_out: Optional[OpsChain] = (),
                param_self=False
                ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def analyze(self, func=None, /, *,
                uid=None, ops_in: Optional[OpsChain] = (), ops_out: Optional[OpsChain] = (),
                param_self=False
                ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def plan(self, func=None, /, *,
             uid=None, ops_in: Optional[OpsChain] = (), ops_out: Optional[OpsChain] = (), param_self=False
             ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def execute(self,
                func=None,
                /, *,
                uid=None,
                ops_in: Optional[OpsChain] = (),
                ops_out: Optional[OpsChain] = (),
                param_self=False
                ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _add_func_decorator(self, func, element_class, *args, **kwargs):
        """ Create the decorator and manage the call w/wo parentheses (ie @decorator vs @decorator()) """
        raise NotImplementedError

    @abstractmethod
    def _add_func(self,
                  # TODO: create an alias
                  func,
                  element_class: Type[Union[Any]],
                  uid=None,
                  ops_in: Optional[OpsChain] = (),
                  ops_out: Optional[OpsChain] = (),
                  param_self=False) -> Any:
        raise NotImplementedError
