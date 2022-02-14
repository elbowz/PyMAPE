from typing import Any
import logging

import json
import aiohttp
import asyncio

from aiohttp.client_exceptions import ClientError

from rx.subject import Subject
from rx.core import Observer, Observable

import mape
from mape.utils import log_task_exception, task_exception

from .api import Port, Notification

logger = logging.getLogger(__name__)


class POSTObserver(Observer):

    def __init__(self, base_url: str, path: str, port: Port = Port.p_in, serializer=None,
                 session: aiohttp.ClientSession = None) -> None:
        self._base_url = base_url
        # TODO: convert path from loop.element => /loops/... (if string start with '/')
        self._path = path
        self._url_path = path
        self._port = port
        self._session = session or aiohttp.ClientSession(base_url)

        # TODO: use _obj_from_row
        from mape.redis_remote import _serializer
        self._serializer = serializer or _serializer
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

            async with self._session.post(self._url_path, data=data, params=params) as resp:
                if resp.status != 200:
                    print("something go wrong")
                    text = await resp.text()
                    print(json.loads(text))

        except aiohttp.client_exceptions.ClientError as e:
            logger.error(e)

    def dispose(self) -> None:
        asyncio.create_task(task_exception(self._session.close()))
        super().dispose()

    def __del__(self):
        self.dispose()
