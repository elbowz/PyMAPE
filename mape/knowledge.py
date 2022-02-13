from aioredis import Redis
from typing import Any, Dict, Type, Union, Tuple, Iterable, List, TypeVar

from mape.remote.redis import (
    RedisKeySpace,
    RedisHash,
    RedisSet,
    RedisList,
    RedisKey,
    RedisSortedSet,
    RedisPriorityQueue,
    RedisQueue,
    RedisLifoQueue,
    Redlock,
    Pickled
)
from mape.constants import RESRVED_PREPEND, RESERVED_SEPARATOR

T = TypeVar('T')


class Knowledge:
    def __init__(self, redis: Redis, prefix: str) -> None:
        self._redis: Redis = redis
        self._prefix: str = prefix + RESERVED_SEPARATOR

        self._keyspace = self.create_keyspace(RESRVED_PREPEND + 'default_keyspace', value_type=Pickled)

    def create_keyspace(self, key: str, value_type: Type[T]):
        return RedisKeySpace(self._redis, self._prefix + key + RESERVED_SEPARATOR, value_type=value_type)

    def create_hash(self, key: str, value_type: Type[T]) -> RedisHash[T]:
        return RedisHash(self._redis, self._prefix + key, value_type=value_type)

    def create_set(self, key: str, value_type: Type[T]) -> RedisSet[T]:
        return RedisSet(self._redis, self._prefix + key, value_type=value_type)

    def create_list(self, key: str, value_type: Type[T]) -> RedisList[T]:
        return RedisList(self._redis, self._prefix + key, value_type=value_type)

    def create_sortedset(self, key: str, value_type: Type[T]) -> RedisSortedSet[T]:
        return RedisSortedSet(self._redis, self._prefix + key, value_type=value_type)

    def create_priorityqueue(self, key: str, value_type: Type[T]) -> RedisPriorityQueue[T]:
        return RedisPriorityQueue(self._redis, self._prefix + key, value_type=value_type)

    def create_queue(self, key: str, value_type: Type[T]) -> RedisQueue[T]:
        return RedisQueue(self._redis, self._prefix + key, value_type=value_type)

    def create_lifoqueue(self, key: str, value_type: Type[T]) -> RedisLifoQueue[T]:
        return RedisLifoQueue(self._redis, self._prefix + key, value_type=value_type)

    def create_redlock(self, key, masters: List[Redis], *args, **kwargs):
        return Redlock(key, masters, *args, **kwargs)

    @property
    def keyspace(self) -> RedisKeySpace[Pickled]:
        return self._keyspace

    @property
    def prefix(self):
        return self._prefix
