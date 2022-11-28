import mape
from mape.constants import RESERVED_PREPEND, RESERVED_SEPARATOR
from mape.knowledge import Knowledge


class Level:
    """
    Level is created only by application usually after a Loop request.
    It aggregates Loops, and is used for Knowledge namespace.
    Loop uid still be unique, and can be directly accessed by App.
    If a Level (ie uid) already exist not throw exception/conflict (like Loop)
    but simply return the existed one (see App.add_default_level())
    """

    def __init__(self, uid: str, app=None) -> None:
        self._uid = uid
        self._app = app or mape.app
        self._loops = dict()

        self._k = Knowledge(self.app.redis, f"k{RESERVED_SEPARATOR}level{RESERVED_SEPARATOR}{self.uid}")

    def add_loop(self, loop):
        uid = loop.uid

        if self.has_loop(uid) or hasattr(self, uid):
            return False

        if loop in loop.app.levels:
            del loop.app.levels.loops[uid]

        loop._level = self
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
        items = path.split(RESERVED_SEPARATOR)
        count_items = len(items)

        if count_items == 1:
            # path: 'loop_uid'
            try:
                return self._loops[items[0]]
            except KeyError as err:
                raise KeyError(f"Loop '{items[0]}' not exist in level '{self.uid}'")
        elif count_items == 2:
            # path: 'loop_uid.element_uid'
            loop = self[items[0]]
            return loop[items[1]]

        raise KeyError(f"Path is malformed {path}")

    def __iter__(self):
        return iter(self._loops.values())

    @property
    def uid(self):
        return self._uid

    def __str__(self) -> str:
        return self.uid

    @property
    def app(self):
        return self._app

    @property
    def loops(self):
        return self._loops

    @property
    def k(self):
        return self._k
