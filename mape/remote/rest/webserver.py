import uvicorn
from multiprocessing import Process

# TODO: format correctly the logger output


class UvicornDaemon:
    def __init__(self, fastapi, host='0.0.0.0', port=6060, log_level='info', **kwargs) -> None:

        args = (fastapi,)
        kwargs = {
            **kwargs,
            'host': host,
            'port': int(port),
            'log_level': log_level
        }

        self._process = Process(target=uvicorn.run, args=args, kwargs=kwargs, daemon=True)

    def start(self):
        self._process.start()

    def stop(self):
        self._process.terminate()

    @property
    def process(self):
        return self._process
