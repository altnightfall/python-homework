import pytest
import fakeredis
import redis
from src.store import Store
import src.store as store_module

@pytest.fixture
def store(monkeypatch):
    fake_redis_instance = fakeredis.FakeRedis(decode_responses=True)
    
    class FakeRedisFactory:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return fake_redis_instance

    monkeypatch.setattr(store_module.redis, "Redis", FakeRedisFactory())
    return Store()


def test_cache_set_and_get(store):
    key = "test_key"
    value = "hello"
    store.cache_set(key, value, 10)
    result = store.cache_get(key)
    assert result == value

def test_get_and_cache_get_are_equivalent(store):
    key = "sample_key"
    value = "value"
    store.cache_set(key, value, 10)
    assert store.get(key) == store.cache_get(key)

def test_cache_overwrite(store):
    key = "overwrite_key"
    store.cache_set(key, "first", 10)
    store.cache_set(key, "second", 10)
    assert store.get(key) == "second"

def test_missing_key_returns_none(store):
    assert store.get("non_existing_key") is None

def test_connection_retry_on_failure(mocker):
    mock_redis = mocker.Mock()
    mock_redis.get.side_effect = redis.RedisError("fail")
    mocker.patch("src.store.redis.Redis", return_value=mock_redis)

    failing_store = store_module.Store()
    with pytest.raises(ConnectionError):
        failing_store.get("any")
