from aioredis import Redis
from typing import Any, Dict, Type, Union, Tuple, Iterable, List, TypeVar
from mape.remote.redis import RedisKeySpace, RedisHash, RedisSet, RedisSortedSet, RedisList, Pickled

T = TypeVar('T')


class Knowledge:
    def __init__(self, redis: Redis, prefix: str) -> None:
        self._redis = redis
        self._prefix = prefix + ':'

        self._keyspace = self.create_keyspace('__keyspace', value_type=Pickled)

    def create_keyspace(self, key: str, value_type: Type[T]):
        return RedisKeySpace(self._redis, self._prefix + key + ':', value_type=value_type)

    def create_hash(self, key: str, value_type: Type[T]) -> RedisHash[T]:
        return RedisHash(self._redis, self._prefix + key, value_type=value_type)

    def create_set(self, key: str, value_type: Type[T]) -> RedisSet[T]:
        return RedisSet(self._redis, self._prefix + key, value_type=value_type)

    def create_sortedset(self, key: str, value_type: Type[T]) -> RedisSortedSet[T]:
        return RedisSortedSet(self._redis, self._prefix + key, value_type=value_type)

    def create_list(self, key: str, value_type: Type[T]) -> RedisList[T]:
        return RedisList(self._redis, self._prefix + key, value_type=value_type)

    @property
    def keyspace(self):
        return self._keyspace
