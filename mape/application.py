from .utils import generate_uid


class App:
    def __init__(self) -> None:
        self._loops = dict()

    def add_loop(self, loop):
        uid = loop.uid or generate_uid(self._loops, prefix=loop.prefix)

        if self.has_loop(uid) or hasattr(self, uid):
            return False

        loop._uid = uid
        loop._app = self
        self._loops[uid] = loop

        return uid

    register = add_loop

    def has_loop(self, loop) -> bool:
        uid = loop.uid if hasattr(loop, 'uid') else loop
        return uid in self._loops

    def __contains__(self, loop):
        return self.has_loop(loop)

    def __getattr__(self, uid):
        """ Allow access (through dot notation) to mape loops.
        note: __getattr__() is called only when no real object attr exist. """
        if uid in self._loops:
            return self._loops[uid]

        super().__getattribute__(uid)

    def __getitem__(self, path: str):
        items = path.split('.')
        count_items = len(items)

        if count_items == 1:
            try:
                return self._loops[items[0]]
            except KeyError as err:
                raise KeyError(f"Loop '{items[0]}' not exist")
        elif count_items == 2:
            loop = self[items[0]]
            return loop[items[1]]

        raise KeyError(f"Path is malformed {path}")

    def __iter__(self):
        return iter(self._loops.values())

