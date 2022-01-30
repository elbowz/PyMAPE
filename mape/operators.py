from __future__ import annotations

from typing import Any, Callable, Optional, Union, Awaitable, Coroutine, NamedTuple

import rx
from rx.subject import Subject
from rx.core import Observer, Observable
from rx.disposable import Disposable, CompositeDisposable
from rx.operators import *

from .base_elements import Element

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


