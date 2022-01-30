import logging
from functools import wraps, partial
from typing import Type, Any, Tuple, List, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple

import mape

from .base_elements import Element, Monitor, Analyze, Plan, Execute, UID_DEF, UID_RANDOM
from .utils import generate_uid
from mape import typing

logger = logging.getLogger(__name__)


class Loop(typing.MapeLoop):
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

        element._uid = uid
        element._loop = self
        self._elements[uid] = element

        return uid

    register = add_element

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

    def monitor(self, func=None, /, *,
                uid=None, ops_in: Optional[typing.OpsChain] = (), ops_out: Optional[typing.OpsChain] = (),
                param_self=False
                ) -> Element:
        return self._add_func_decorator(func, Monitor, uid=uid, ops_in=ops_in, ops_out=ops_out, param_self=param_self)

    def analyze(self, func=None, /, *,
                uid=None, ops_in: Optional[typing.OpsChain] = (), ops_out: Optional[typing.OpsChain] = (),
                param_self=False
                ) -> Element:
        return self._add_func_decorator(func, Analyze, uid=uid, ops_in=ops_in, ops_out=ops_out, param_self=param_self)

    def plan(self, func=None, /, *,
             uid=None, ops_in: Optional[typing.OpsChain] = (), ops_out: Optional[typing.OpsChain] = (), param_self=False
             ) -> Element:
        return self._add_func_decorator(func, Plan, uid=uid, ops_in=ops_in, ops_out=ops_out, param_self=param_self)

    def execute(self,
                func=None,
                /, *,
                uid=None,
                ops_in: Optional[typing.OpsChain] = (),
                ops_out: Optional[typing.OpsChain] = (),
                param_self=False
                ) -> Element:
        return self._add_func_decorator(func, Execute, uid=uid, ops_in=ops_in, ops_out=ops_out, param_self=param_self)

    def _add_func_decorator(self, func, element_class, *args, **kwargs):
        """ Create the decorator and manage the call w/wo parentheses (ie @decorator vs @decorator()) """
        if func is None:
            # Called as @decorator(), with parentheses.
            # Return a function with all args set except 'func',
            # the second call (ie. @decorator(args)(func)) will set 'func'.
            return partial(self._add_func_decorator, element_class=element_class, *args, **kwargs)

        # Called as @decorator, without parentheses
        return self._add_func(func, element_class, *args, **kwargs)

    def _add_func(self,
                  # TODO: create an alias
                  func,
                  element_class: Type[Union[Any]],
                  uid=UID_DEF,
                  ops_in: Optional[typing.OpsChain] = (),
                  ops_out: Optional[typing.OpsChain] = (),
                  param_self=False) -> Element:

        # discover what parameters (name and default) has function signature
        # import inspect
        # for param in inspect.signature(func).parameters.values():
        #     print("param_name", param.name, param.default)

        if uid == UID_DEF:
            uid = func.__name__
        # UID_RANDOM or str is managed directly by Element()

        # if uid is None and self.has_element(func.__name__):
        #     # Uid not specified and fallback name function not usable (conflict).
        #     element_uid = generate_uid(self._elements, prefix=element_class.prefix)
        #     logging.warning(f"Function_name '{func.__name__}' already used in '{self.uid}' loop. "
        #                     f"Used '{element_uid}' as uid")
        #
        # elif self.has_element(uid):
        #     raise ValueError(f"Element uid '{element_uid}' in '{self.uid}' loop already taken,"
        #                      f" please provide an alternative uid, or leave blank for an autogenerated")
        #
        # elif hasattr(self, element_uid):
        #     raise ValueError(f"Element uid '{element_uid}' attr name reserved in object loop.")

        element: Element = element_class(loop=self, uid=uid, ops_in=ops_in, ops_out=ops_out)

        param_self and element.add_param_to_on_next_call({'self': element})
        setattr(element, '_on_next', func)
        # or: element._on_next = func

        # @wraps(func)
        # def wrapper(*args, **kwargs):
        #     log.log(level, logmsg)
        #     return func(*args, **kwargs)
        # return wrapper
        return element
