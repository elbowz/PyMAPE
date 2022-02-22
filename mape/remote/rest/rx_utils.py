from __future__ import annotations

import logging
import json
import aiohttp
import asyncio

from typing import Any
from functools import partial
from aiohttp.client_exceptions import ClientError
from rx.core import Observer, Observable

import mape
from mape.utils import log_task_exception, task_exception
from mape.constants import RESERVED_SEPARATOR

from .api import Port, Notification, element_notify_path
from ..de_serializer import obj_to_raw, obj_from_raw, Pickled

logger = logging.getLogger(__name__)

# TODO:
# * better implemented with a queue (like PubObserver) to preserve notifications order


def _element_path2url_path(element_path):
    loop_uid, element_uid = element_path.split(RESERVED_SEPARATOR)
    return element_notify_path.format(loop_uid=loop_uid, element_uid=element_uid)


class POSTObserver(Observer):
    def __init__(self,
                 base_url: str,
                 path: str,
                 port: Port = Port.p_in,
                 serializer=None,
                 session: aiohttp.ClientSession = None) -> None:
        self._base_url = base_url

        try:
            self._path = path if path.startswith('/') else _element_path2url_path(path)
        except ValueError as e:
            logger.error(f"Malformed element_path: '{path}'")

        self._port = port
        self._session = session or aiohttp.ClientSession(base_url)
        self._serializer = serializer or partial(obj_to_raw, Pickled)
        # self._queue = asyncio.Queue()

        super().__init__()

    def _on_next_core(self, value: Any) -> None:
        asyncio.create_task(self.post(value, Notification.next))

    def _on_error_core(self, error: Exception) -> None:
        asyncio.create_task(self.post(error, Notification.error))

    def _on_completed_core(self) -> None:
        asyncio.create_task(self.post(None, Notification.completed))

    @log_task_exception
    async def post(self, value, notification: Notification):
        try:
            data = self._serializer(value)
            params = {'port': self._port.value, 'notification': notification.value}

            async with self._session.post(self._path, data=data, params=params) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Response from '{self._path}' status {resp.status}: '{json.loads(text)}'")

        except aiohttp.client_exceptions.ClientError as e:
            logger.error(e)

    def dispose(self) -> None:
        asyncio.create_task(task_exception(self._session.close()))
        super().dispose()

    def __del__(self):
        self.dispose()


# TODO: to finish
import rx
from rx.disposable import Disposable
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response


class PostObservable(Observable):
    def __init__(self, path, deserializer=None, fastapi: FastAPI | None = None) -> None:
        self._path = path
        self._fastapi = fastapi or mape.fastapi
        self._deserializer = deserializer or partial(obj_from_raw, Pickled)

        self._task = None

        def on_subscribe(observer, scheduler):

            async def on_next1(request: Request):
                print(await request.body())
                return await request.body()
                # observer.on_next(value)

            self._fastapi.post(self._path, response_class=Response)(on_next1)

            print("subscribed", self._path)

            return Disposable()

        self._auto_connect = rx.create(on_subscribe).pipe(ops.dematerialize(), ops.share())
        super().__init__()

    def _subscribe_core(self, observer, scheduler=None):
        return self._auto_connect.subscribe(observer, scheduler=scheduler)

    # TODO: re-running create unpredictable error (endpoint appear and disappear
    # def close(self):
    #     # Find the route by path
    #     # try:
    #     route = [route for route in self._fastapi.routes if route.path == self._path]
    #     if len(route):
    #         self._fastapi.routes.remove(route[0])
    #     # except (IndexError, ValueError) as e:
    #     #     # already removed (ie. webserver shutdown)
    #     #     pass
    #
    # def __del__(self):
    #     self.close()