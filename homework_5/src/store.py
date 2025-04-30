import redis
import time
import logging

RETRY_COUNT = 3
RETRY_DELAY = 0.1

class Store:
    def __init__(self, host='localhost', port=6379, db=0, timeout=1):
        self.host = host
        self.port = port
        self.db = db
        self.timeout = timeout
        self._connect()

    def _connect(self):
        self.redis = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            socket_timeout=self.timeout,
            socket_connect_timeout=self.timeout,
            decode_responses=True  # чтобы не было байт в ответах
        )

    def _try(self, func, *args, **kwargs):
        for attempt in range(RETRY_COUNT):
            try:
                return func(*args, **kwargs)
            except redis.RedisError as e:
                logging.warning(f"Redis error: {e}, attempt {attempt+1}")
                time.sleep(RETRY_DELAY)
                self._connect()
        raise ConnectionError("Could not connect to Redis after retries")

    def get(self, key):
        return self._try(self.redis.get, key)

    def cache_get(self, key):
        return self._try(self.redis.get, key)

    def cache_set(self, key, value, expire=60):
        return self._try(self.redis.setex, key, expire, value)
