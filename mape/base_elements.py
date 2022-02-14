from __future__ import annotations

import logging
import inspect
import asyncio
from typing import Type, Any, List, Tuple, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple, Final, overload, TypeVar
from enum import Flag, Enum
from functools import partial, wraps

import rx
from rx.subject import Subject
from rx.core import Observer, Observable, ConnectableObservable, typing as rx_typing
from rx.disposable import Disposable, CompositeDisposable
from rx import operators as ops
from dataclasses import dataclass, field

import mape
from mape import typing
from mape.constants import RESERVED_SEPARATOR
from .utils import init_logger, LogObserver, GenericObject, caller_module_name, task_exception, aio_call

logger = logging.getLogger(__name__)


class BaseMapeElementTODELETE:
    """
    Encapsulate a ConnectableObservable like
    It has multiple source/in ports Subject (ie external write/read on stream)
    and multiple sink/out ports Observable (ie external read on stream)
    """

    def __init__(self) -> None:
        self._scheduler = None

        # Input port
        self._source: Subject = Subject()
        self._source_dispose = self.start(self._source)

        # Default sink "do nothing"
        self._sink: Observer = Observer()
        # Output port
        self._observable = rx.create(self._on_subscribe).pipe(
            # output transformation
            # ops.do(LogObserver('out')),
            ops.share()
        )

    """ SOURCE """

    def start(self, source: Subject = None):
        source = source or self._source

        return source.pipe(
            # output transformation
            ops.do(LogObserver('in')),
        ).subscribe(
            on_next=self._on_next,
            on_error=self._on_error,
            on_completed=self._on_completed
        )

    def stop(self) -> None:
        logger.debug('stop')
        self._source_dispose.dispose()

    def port(self, port='default'):
        return self._source

    __call__ = port

    def __getitem__(self, key='default'):
        return self.port(key)

    def _on_next(self, value: Any) -> None:
        self._sink.on_next(value)

    def _on_error(self, error: Exception) -> None:
        logger.error(error)
        # self._sink.on_error(error)

    def _on_completed(self) -> None:
        logger.warning('stream completed')
        # self._sink.on_completed()

    """ SINK """

    def subscribe(self, *args, **kwargs):
        # TODO: DEFINE MULTIPORT?!
        if 'port' in kwargs:
            print(kwargs['port'])
            del kwargs['port']
        return self._observable.subscribe(*args, **kwargs)

    def pipe(self, *operators: Callable[['Observable'], Any]) -> Any:
        return self._observable.pipe(*operators)

    def _on_subscribe(self, observer, scheduler):
        self._sink = observer
        self._scheduler = scheduler

        self._sink.on_next("Sent on first subscription")

        return Disposable(self.on_unsubscribe)

    def on_unsubscribe(self):
        """ Only subscriber have disposed/ended the subscription """
        logger.debug('on_unsubscribe')


class UID(Enum):
    RANDOM = None
    DEF = 1

    # TODO: remove, because never used
    @dataclass
    class MANUAL:
        value: str = ''


# TODO: use Pydantic (in general for dataclass and validation (ie also setting)
@dataclass
class Port:
    # TODO: add method to manipulate operators (append, prepend, etc...) and update pipe/input/subscribe?!
    input: Subject = None
    pipe: Observable = None
    operators: List[Callable[[Any], Any]] = field(default_factory=lambda: [])
    output: Subject = None
    disposable: Disposable = None


# TODO:
#  * inherit from Subject?
#  * single pipe from p_in to p_out and in the middle ops.through (ie on_next, on_error...)
#  * use a ConnectableObservable instead and exploit the .connect(), implementing .disconnect() ?!
#    inspiration: https://github.com/ReactiveX/RxPY/blob/release/v1.6.x/rx/backpressure/pausable.py
class Element(Observable, Observer, rx_typing.Subject):
    # TODO: pass as argument to _process_msg, instead of only move_on
    # evaluate if is it necessary:
    #  * is raise exception inside _process_msg the same that pass error
    #  * return instead of on_complete()? ...we need on_complete?!
    # @dataclass(frozen=True)
    # class ProcessFuncData:
    #     next: Callable
    #     error: Callable
    #     completed: Callable
    prefix: str = ''

    class Debug(Flag):
        DISABLE = 1
        IN = 2
        OUT = 4

    def __init__(self,
                 loop: typing.MapeLoop,
                 uid: str | UID = None,
                 ops_in: Optional[typing.OpsChain] = (),
                 ops_out: Optional[typing.OpsChain] = ()
                 ) -> None:
        uid = uid if uid != UID.DEF else self.__class__.__name__
        self._uid = uid if not hasattr(uid, 'value') else uid.value

        self._loop: mape.Loop = loop
        self._aio_loop = mape.aio_loop or asyncio.get_event_loop()
        self.is_running = False
        self._debug = GenericObject()

        # Add Element to loop
        self._uid = self.add_to_loop(loop)

        if not self._uid:
            raise ValueError(f"'{uid}' already taken, or name is protected")

        # Accept pipe(), ops(), (ops(),)
        # TODO: I think is not so good, and not always it works
        # hint:
        #   >>> seq = seq if isinstance(seq, (List, Tuple)) else (seq,)
        #   >>> sqe = seq if isinstance(seq, Sequence) else (seq,) # take also string (not good)
        #   >>> routes: typing.Sequence[BaseRoute] = None,
        #   >>> self.routes = [] if routes is None else list(routes)
        ops_in = list(ops_in) if isinstance(ops_in, Tuple) else [ops_in]
        ops_out = list(ops_out) if isinstance(ops_out, Tuple) else [ops_out]

        # Port in and out
        self._p_in = Port(input=Subject(), operators=ops_in)
        self._p_out = Port(input=Subject(), operators=ops_out, output=Subject())

        Observable.__init__(self)
        Observer.__init__(self, self._p_in.input.on_next, self._p_in.input.on_error, self._p_in.input.on_completed)

    async def _aio_init(self):
        """ Stuff to init with await """
        pass

    def __await__(self):
        return self._aio_init().__await__()

    def add_to_loop(self, loop: mape.Loop):
        return loop.add_element(self)

    move_to_loop = add_to_loop

    def debug(self, lvl: Element.Debug = Debug.DISABLE, module_name=None):
        module_name = module_name or caller_module_name()

        if Element.Debug.IN in lvl:
            self._debug.in_dispose = self._p_in.input.subscribe(
                LogObserver(f"in > [{self._loop.uid}{RESERVED_SEPARATOR}{self.uid}]", module_name)
            )
        elif hasattr(self._debug, 'in_dispose'):
            self._debug.in_dispose.dispose()

        if Element.Debug.OUT in lvl:
            self._debug.out_dispose = self._p_out.output.subscribe(
                LogObserver(f"[{self._loop.uid}{RESERVED_SEPARATOR}{self.uid}] > out", module_name)
            )
        elif hasattr(self._debug, 'out_dispose'):
            self._debug.out_dispose.dispose()

    def subscribe(self, observer: Optional[Union[rx_typing.Observer, rx_typing.OnNext]] = None,
                  on_error: Optional[rx_typing.OnError] = None, on_completed: Optional[rx_typing.OnCompleted] = None,
                  on_next: Optional[rx_typing.OnNext] = None, *,
                  scheduler: Optional[rx_typing.Scheduler] = None, param: Any = None) -> rx_typing.Disposable:

        # print(self.uid, observer, param)

        return super().subscribe(observer, on_error, on_completed, on_next, scheduler=scheduler)

    def _subscribe_core(self, observer, scheduler=None):
        """ Things to do on each subscribe """
        subscription = self._p_out.output.subscribe(observer, scheduler=scheduler)
        return CompositeDisposable(Disposable(lambda _: self.on_unsubscribe(observer)), subscription)

    def on_unsubscribe(self, observer):
        """ On each subscriber have disposed/ended the subscription """
        logger.debug(f"on_unsubscribe", observer)

    """ Start and stop element. 
    Only port_in stay readable, the rest is frozen (ie. no item transit).
    Good methods to extend for (de)allocate/start/stop internal element resources """

    def start(self, scheduler=None):
        if not self.is_running:
            # TODO: debug can be pre-pend here as ops.do_action() instead of subscribe ?!
            self._p_in.pipe = self._p_in.input.pipe(
                ops.filter(lambda item: not isinstance(item, typing.CallMethod)),
                ops.do_action(lambda item: isinstance(item, typing.Message) and item.add_hop(self)),
                *self._p_in.operators
            )

            sub_message = self._p_in.pipe.subscribe(
                lambda value: self._on_next(value, self._p_out.input.on_next),
                # self._on_next,
                self._on_error,
                self._on_completed,
                scheduler=scheduler
            )

            # TODO: implement the logic of do_action (ie. real call).
            # Maybe can be un external utility where pass self
            sub_method_call = self._p_in.input.pipe(
                ops.filter(lambda item: isinstance(item, typing.CallMethod)),
                ops.do_action(lambda item: item.exec(self))
            ).subscribe(scheduler=scheduler)

            self._p_in.disposable = CompositeDisposable(sub_message, sub_method_call)

            self._p_out.pipe = self._p_out.input.pipe(*self._p_out.operators)
            self._p_out.disposable = self._p_out.pipe.subscribe(self._p_out.output, scheduler=scheduler)

            self.is_running = True

        return Disposable(self.stop)

    def stop(self):
        if self.is_running:
            self._p_out.disposable.dispose()
            self._p_in.disposable.dispose()

            self.is_running = False

    def dispose(self) -> None:
        self.stop()
        # Uncomment (should) means that observer need to RE-subscribe
        # self._p_out.output.dispose()
        # self._p_in.input.dispose()
        # super().dispose()

    """ Called after [port in] => [pipe in] => [_on_next()] => [pipe out] => [port out] """

    def _on_next(self, value: Any, on_next: Optional[Callable] = None, *args, **kwargs) -> Any:
        """ Override to add your business logic """
        on_next = on_next or self._p_out.input.on_next
        on_next(value)

    # def _process_msg(self, value: Any move_on: Callable, *args, **kwargs):
    #     """ Subscribe for add your business logic """
    #     move_on(value)

    def __call__(self, value, *args, **kwargs):
        return self._on_next(value, on_next=self._p_out.input.on_next, *args, **kwargs)

    def _on_error(self, error: Exception) -> None:
        self._p_out.input.on_error(error)

    def _on_completed(self) -> None:
        self._p_out.input.on_completed()

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def loop(self) -> mape.Loop:
        return self._loop

    @property
    def path(self) -> str:
        return f"{self.loop.uid}.{self.uid}"

    """ Port in and out aliases """

    @property
    def p_in(self):
        return self._p_in.input

    @property
    def p_out(self):
        return self._p_out.output

    @property
    def port_in(self):
        return self.p_in

    @property
    def port_out(self):
        return self.p_out

    @property
    def source(self):
        return self.p_in

    @property
    def sink(self):
        return self.p_out


class StartOnSubscribe(Element):
    def _subscribe_core(self, observer, scheduler=None):
        subscribe = super()._subscribe_core(observer, scheduler)
        super().start(scheduler=scheduler)

        return subscribe


class StartOnInit(Element):
    def __init__(self,
                 loop,
                 uid: str,
                 ops_in: Optional[Tuple] = (),
                 ops_out: Optional[Tuple] = (),
                 scheduler=None
                 ) -> None:
        super().__init__(loop, uid, ops_in, ops_out)
        super().start(scheduler=scheduler)


class Monitor(Element):
    prefix: str = 'm_'


class Analyze(StartOnSubscribe):
    prefix: str = 'a_'


class Plan(StartOnSubscribe):
    prefix: str = 'p_'


class Execute(StartOnInit):
    prefix: str = 'e_'


""" Allow display correct signature in IDE """
# ~/.local/share/JetBrains/IntelliJIdea2021.3/python/helpers/typeshed/stdlib/dataclasses.pyi

@overload
def to_element_cls(func: Callable) -> Type[Element]: ...


@overload
def to_element_cls(func: None) -> Callable[[Callable], Type[Element]]: ...


@overload
def to_element_cls(
        *,
        element_class=...,
        default_uid: str | UID = ...,
        default_ops_in: Optional[typing.OpsChain] = ...,
        default_ops_out: Optional[typing.OpsChain] = ...,
        param_self: bool = ...
) -> Type[Element]: ...


""" END  """


def to_element_cls(func=None, /, *,
                   element_class=Element,
                   default_uid: str | UID = UID.DEF,
                   default_ops_in: Optional[typing.OpsChain] = (),
                   default_ops_out: Optional[typing.OpsChain] = (),
                   param_self: bool = False) -> Type[Element] | Callable[..., Type[Element]]:
    """ Create the decorator and manage the call w/wo parentheses (ie @decorator vs @decorator()) """
    if func is None:
        # Called as @decorator(), with parentheses.
        # Return a function with all args set except 'func',
        # the second call (ie. @decorator(args)(func)) will set 'func'.
        return partial(to_element_cls,
                       element_class=element_class,
                       default_uid=default_uid,
                       default_ops_in=default_ops_in,
                       default_ops_out=default_ops_out,
                       param_self=param_self)

    # Called as @decorator, without parentheses
    return make_func_class(func, element_class, default_uid, default_ops_in, default_ops_out, param_self)


# TODO: maybe can be passed *args, **kwargs (since default_uid)
def make_func_class(func: Callable | Coroutine,
                    element_class: Type[Element],
                    default_uid: str | UID = UID.DEF,
                    default_ops_in: Optional[typing.OpsChain] = (),
                    default_ops_out: Optional[typing.OpsChain] = (),
                    param_self: bool = False
                    ) -> Type[Element]:

    if default_uid == UID.DEF:
        default_uid = func.__name__

    # Discover what parameters (name and default) has function signature
    # import inspect
    # for param in inspect.signature(func).parameters.values():
    #     print("param_name", param.name, param.default)

    class ElementFunc(element_class):
        def __init__(self,
                     loop: mape.Loop,
                     uid: str | UID = default_uid,
                     ops_in: Optional[typing.OpsChain] = default_ops_in,
                     ops_out: Optional[typing.OpsChain] = default_ops_out
                     ) -> None:
            super().__init__(loop, uid, ops_in, ops_out)

            # Additional params/kwargs passed to func()
            self._on_next_opt_kwargs = {}

            if param_self:
                self._on_next_opt_kwargs = {'self': self}

            # TODO: alternative _on_next definition to test
            # self.__class__._on_next = func

        @wraps(func)
        def _on_next(self, *args, **kwargs) -> Any | Awaitable:
            new_kwargs = {**self._on_next_opt_kwargs, **kwargs}

            if inspect.iscoroutinefunction(func):
                # The func execution is put in a task (ie parallel/background)
                coro = task_exception(func(*args, **new_kwargs))
                return self._aio_loop.create_task(coro)
            else:
                return func(*args, **new_kwargs)

        def add_param_to_on_next_call(self, kwargs):
            """ Pass a dict with key: value (as param=value) to pass during _on_next() calling. """
            self._on_next_opt_kwargs = kwargs

    # Code used when we act on object (and not class) level
    # Bound as a real "object method" passing self as first arg
    # func = types.MethodType(func, element)
    # setattr(element, '_on_next', func)
    # or: element._on_next = func

    return ElementFunc


# Dinamically add to module
# import sys
# sys.modules[__name__].ciao = "ciao"


to_monitor_cls = partial(to_element_cls, element_class=Monitor)
to_analyze_cls = partial(to_element_cls, element_class=Analyze)
to_plan_cls = partial(to_element_cls, element_class=Plan)
to_execute_cls = partial(to_element_cls, element_class=Execute)
