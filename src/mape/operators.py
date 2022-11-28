from __future__ import annotations

from typing import Any, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple, Tuple

import rx
from rx.subject import Subject
from rx.core import Observer, Observable
from rx.disposable import Disposable, CompositeDisposable
from rx.operators import *

import mape
from .base_elements import Element
from .typing import Mapper, OpsChain, DestMapper, Message

MapeElement = Union[Subject, Element]


def through(subject: MapeElement):
    """ Item pass through the subject """

    def _through(source):
        def subscribe(observer, scheduler=None):
            source_dispose = source.subscribe(subject, scheduler=scheduler)
            subject_dispose = subject.subscribe(observer, scheduler=scheduler)

            return CompositeDisposable(source_dispose, subject_dispose)

        return Observable(subscribe)

    return _through


sitm = through


def group_and_pipe(operators: OpsChain, key_mapper: Mapper = None):
    key_mapper = key_mapper or (lambda item: item.src)
    ops_in = list(pipe) if isinstance(pipe, Tuple) else [pipe]

    def _group_and_pipe(source):
        def subscribe(observer, scheduler=None):
            return source.pipe(
                group_by(key_mapper),
                flat_map(
                    lambda grp: grp.pipe(*operators)
                )).subscribe(
                observer.on_next,
                observer.on_error,
                observer.on_completed,
                scheduler)

        return rx.create(subscribe)

    return _group_and_pipe


reverse_proxy = group_and_pipe


def _gateway_dest_mapper(item: Message):
    return mape.app[item.dst]


def gateway(dest_mapper: DestMapper = None):
    dest_mapper = dest_mapper or _gateway_dest_mapper

    def _gateway(source):
        def subscribe(observer, scheduler=None):
            from collections.abc import Iterable

            def on_next(item):
                dests = dest_mapper(item)
                if not isinstance(dests, Iterable):
                    # Convert dest in a tuple
                    dests = (dests,)

                for dest in dests:
                    dest.on_next(item)
                observer.on_next(item)

            def on_error(error):
                observer.on_error(error)

            def on_completed():
                observer.on_completed()

            return source.subscribe(
                on_next,
                on_error,
                on_completed,
                scheduler)

        return rx.create(subscribe)

    return _gateway


router = gateway

