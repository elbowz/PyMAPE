from __future__ import annotations

import logging
from typing import Callable, Dict, Any, Mapping, Tuple, List, Iterable

from rx.core import Observer
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

from mape.typing import Message

logger = logging.getLogger(__name__)


def _fields_mapper(item, key='value'):
    if hasattr(item, key):
        value = getattr(item, key)
    elif isinstance(item, Mapping):
        value = item.get(key)
    else:
        value = item

    return key, value


class InfluxObserver(Observer):
    def __init__(self,
                 measurement: str | None = None,
                 tags: Iterable | Iterable[Iterable] | None = None,
                 fields_mapper: Callable | None = None,
                 bucket: str | None = None,
                 is_raw: bool = False,
                 write_options: WriteOptions = ASYNCHRONOUS,
                 client: InfluxDBClient | None = None
                 ) -> None:
        from . import _config

        self._measurement = measurement
        self._tags = tags
        self._fields_mapper = fields_mapper or _fields_mapper
        self._bucket = bucket or _config['bucket']
        self._is_raw = is_raw
        self._write_options = write_options
        self._org = _config['org']
        self._client = client or InfluxDBClient(
            **{k: _config[k] for k in ('url', 'token', 'org', 'debug') if k in _config}
        )
        self._write_api = self._client.write_api(write_options=write_options)

        if self._tags and not isinstance(self._tags[0], (Tuple, List)):
            self._tags = (self._tags,)

        super().__init__()

    def _on_next_core(self, item: Any) -> None:
        if self._is_raw:
            self._write_api.write(self._bucket, self._org, record=item)
        else:
            measurement = self._measurement or type(item).__name__
            point = Point(measurement)

            if not self._tags and hasattr(item, '__dict__'):
                value_as_dict = item.__dict__
                tags = [(k, value_as_dict[k]) for k in value_as_dict if k not in ('value', 'timestamp')]
            else:
                tags = self._tags or list()

            for tag, value in tags:
                point.tag(tag, value)

            fields = self._fields_mapper(item)
            if not isinstance(fields[0], (Tuple, List)):
                fields = (fields,)

            for field, value in fields:
                point.field(field, value)

            logger.debug(f"InfluxDB write: {point.to_line_protocol()}")
            self._write_api.write(self._bucket, self._org, record=point)

    def dispose(self) -> None:
        self._client.__del__()
        super().dispose()

    def __del__(self):
        self.dispose()