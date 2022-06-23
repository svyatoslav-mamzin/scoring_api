import redis
import logging
from time import sleep

from constants import HOST, PORT, SOCKET_TIMEOUT


class Store:
    def __init__(self, retry=5, cache_time=60):
        self.cache = redis.StrictRedis(host=HOST,
                                       port=PORT,
                                       db=0,
                                       socket_timeout=SOCKET_TIMEOUT,
                                       charset="utf-8",
                                       decode_responses=True
                                       )
        self.store = redis.StrictRedis(host=HOST,
                                       port=PORT,
                                       db=1,
                                       socket_timeout=SOCKET_TIMEOUT,
                                       charset="utf-8",
                                       decode_responses=True
                                       )
        self.cache_time = cache_time
        self.retry = retry
        self.attempts = 0

    def do_store(self, command, *args):
        while self.attempts <= self.retry:
            try:
                value = getattr(self.store, command)(*args)
            except Exception as e:
                logging.info(f"Redis error: {e}, retry...")
                self.attempts += 1
                sleep(1)
            else:
                return value
        raise redis.exceptions.ConnectionError

    def get(self, key):
        return self.do_store('get', key)

    def set(self, key, value):
        return self.do_store('set', key, value)

    def cache_get(self, key):
        return self.cache.get(key)

    def cache_set(self, key, value, cache_time=None):
        cache_time = cache_time if cache_time else self.cache_time
        self.cache.setex(key, time=cache_time,
                         value=value)
        return True
