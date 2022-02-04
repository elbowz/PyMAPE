from __future__ import annotations

import functools
import logging
import inspect
from functools import wraps, partial
from typing import Type, Any, Tuple, List, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple, TypeVar
import types

import mape

from .base_elements import Element, Monitor, Analyze, Plan, Execute, UID, to_element_cls, make_func_class
from .utils import generate_uid
from .typing import MapeLoop, OpsChain

logger = logging.getLogger(__name__)

TElement = TypeVar('TElement')


class Loop(MapeLoop):
    prefix: str = 'l_'

    def __init__(self, uid: str = None, app=None) -> None:
        self._uid = uid
        self._elements = dict()
        self._app = app or mape.app

        # Add Loop to App
        self._uid = self.add_to_app(app)

        if not self._uid:
            raise ValueError(f"'{uid}' already taken, or name is protected")

    def add_to_app(self, app):
        return self._app.add_loop(self)

    move_to_app = add_to_app

    def add_element(self, element):
        uid = element.uid or generate_uid(self._elements, prefix=element.prefix)

        if self.has_element(uid) or hasattr(self, uid):
            return False

        if element in element._loop:
            del element.loop.elements[element.uid]

        element._uid = uid
        element._loop = self
        self._elements[uid] = element

        return uid

    def has_element(self, element):
        uid = element.uid if hasattr(element, 'uid') else element
        return uid in self._elements

    def __contains__(self, element):
        return self.has_element(element)

    def __getattr__(self, uid):
        """ Allow access (through dot notation) to mape elements.
        note: __getattr__() is called only when no real object attr exist. """
        if uid in self._elements:
            return self._elements[uid]

        super().__getattribute__(uid)

    def __getitem__(self, uid):
        try:
            return self._elements[uid]
        except KeyError as err:
            raise KeyError(f"Element '{uid}' not exist in '{self._uid}' loop")

    def __iter__(self):
        return iter(self._elements.values())

    @property
    def uid(self):
        return self._uid

    @property
    def app(self):
        return self._app

    @property
    def elements(self):
        return self._elements

    def monitor(self,
                func: Callable = None, /, *,
                uid: str | UID = UID.DEF,
                ops_in: Optional[OpsChain] = (),
                ops_out: Optional[OpsChain] = (),
                param_self: bool = False
                ) -> Monitor:
        """ Function decorator """

        return self.add_func(func,
                             element_class=Monitor,
                             uid=uid,
                             ops_in=ops_in,
                             ops_out=ops_out,
                             param_self=param_self)

    def analyze(self,
                func: Callable = None, /, *,
                uid: str | UID = UID.DEF,
                ops_in: Optional[OpsChain] = (),
                ops_out: Optional[OpsChain] = (),
                param_self: bool = False
                ) -> Analyze:
        """ Function decorator """

        return self.add_func(func,
                             element_class=Analyze,
                             uid=uid,
                             ops_in=ops_in,
                             ops_out=ops_out,
                             param_self=param_self)

    def plan(self,
             func: Callable = None, /, *,
             uid: str | UID = UID.DEF,
             ops_in: Optional[OpsChain] = (),
             ops_out: Optional[OpsChain] = (),
             param_self: bool = False
             ) -> Plan:
        """ Function decorator """

        return self.add_func(func,
                             element_class=Plan,
                             uid=uid,
                             ops_in=ops_in,
                             ops_out=ops_out,
                             param_self=param_self)

    def execute(self,
                func: Callable = None, /, *,
                uid: str | UID = UID.DEF,
                ops_in: Optional[OpsChain] = (),
                ops_out: Optional[OpsChain] = (),
                param_self: bool = False
                ) -> Execute:
        """ Function decorator """

        return self.add_func(func,
                             element_class=Execute,
                             uid=uid,
                             ops_in=ops_in,
                             ops_out=ops_out,
                             param_self=param_self)

    # Alternative method to declare execute, but missing signature/type hint
    # execute_test = functools.partialmethod(add_func, element_class=Execute)

    # TODO: provare con l'overload una per ElementFunc e una per tutte le altre classi
    def register(self,
                 cls: Type[TElement] = None,
                 /, *,
                 uid: str | UID = UID.DEF,
                 ops_in: Optional[OpsChain] = (),
                 ops_out: Optional[OpsChain] = ()
                 ) -> Type[TElement] | TElement:
        """ Class decorator """
        if cls is None:
            return partial(self.register,
                           uid=uid,
                           ops_in=ops_in,
                           ops_out=ops_out)

        kwargs = {}

        args_name = inspect.signature(cls.__init__).parameters.keys()

        # Append (if present in the signature) additional cls constructor args for obj initialization
        if 'uid' in args_name and cls.__name__ != 'ElementFunc':
            # Avoid if Element cls generated by func.
            # uid with UID.DEF already set with func name
            kwargs['uid'] = uid
        if 'ops_in' in args_name and ops_in:
            kwargs['ops_in'] = ops_in
        if 'ops_out' in args_name and ops_out:
            kwargs['ops_out'] = ops_out

        element = cls(loop=self, **kwargs)

        return element if cls.__name__ == 'ElementFunc' else cls

    register_cls = register

    def add_func(self,
                 func: Callable = None,
                 /, *,
                 element_class: Type[TElement] = Element,
                 uid: str | UID = UID.DEF,
                 ops_in: Optional[OpsChain] = (),
                 ops_out: Optional[OpsChain] = (),
                 param_self: bool = False) -> TElement:
        """ Function decorator """

        if func is None:
            return partial(self.add_func,
                           element_class=element_class,
                           uid=uid,
                           ops_in=ops_in,
                           ops_out=ops_out,
                           param_self=param_self)

        cls = make_func_class(func,
                             element_class=element_class,
                             default_uid=uid,
                             default_ops_in=ops_in,
                             default_ops_out=ops_out,
                             param_self=param_self)

        return self.register(cls)
