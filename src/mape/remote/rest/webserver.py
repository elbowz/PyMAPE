import asyncio

from uvicorn import Config, Server
from multiprocessing import Process

# TODO: format correctly the logger output


class UvicornDaemon:
    def __init__(self, app, loop, host='0.0.0.0', port=6060, log_level='info', **kwargs) -> None:
        self._loop = loop

        kwargs = {
            'app': app,
            'host': host,
            'port': int(port),
            'log_level': log_level,
            **kwargs
        }

        config = Config(**kwargs)
        self._server = Server(config)
        self._loop.create_task(self._server.serve())

    def stop(self):
        self._loop.create_task(self._server.shutdown())

    @property
    def config(self):
        return self._server.config

