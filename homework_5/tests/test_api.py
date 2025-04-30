import unittest
from datetime import datetime
import hashlib

from src.api import method_handler, INVALID_REQUEST, FORBIDDEN, OK
from tests.utils import cases


class MockStore:
    def __init__(self):
        self._data = {}
        self._cache = {}

    def get(self, key):
        return self._data.get(key)

    def cache_get(self, key):
        return self._cache.get(key)

    def cache_set(self, key, value, expire):
        self._cache[key] = value


class TestAPIMethodHandler(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    def get_response(self, request):
        return method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    @cases([
        {"account": "test", "login": "user", "method": "online_score", "token": "", "arguments": {}},
        {"account": "x", "login": "admin", "method": "online_score", "token": "wrong", "arguments": {}},
        {"account": "", "login": "user", "method": "clients_interests", "token": "", "arguments": {}}
    ])
    def test_bad_auth(self, case):
        response, code = self.get_response(case)
        assert code == FORBIDDEN

    def test_invalid_method(self):
        token = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + "42").encode()).hexdigest()
        request = {
            "account": "x",
            "login": "admin",
            "method": "unknown_method",
            "token": token,
            "arguments": {}
        }
        response, code = self.get_response(request)
        assert code == INVALID_REQUEST

    def test_valid_admin_score(self):
        token = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + "42").encode()).hexdigest()
        request = {
            "account": "any",
            "login": "admin",
            "method": "online_score",
            "token": token,
            "arguments": {
                "phone": "71234567890",
                "email": "admin@example.com"
            }
        }
        response, code = self.get_response(request)
        assert code == OK
        assert response["score"] == 42

    def test_valid_user_score(self):
        account = "test"
        login = "user"
        token = hashlib.sha512((account + login + "Otus").encode()).hexdigest()
        request = {
            "account": account,
            "login": login,
            "method": "online_score",
            "token": token,
            "arguments": {
                "phone": "71234567890",
                "email": "user@example.com"
            }
        }
        self.store = MockStore()
        response, code = self.get_response(request)
        assert code == OK
        assert isinstance(response["score"], (float, int))
        assert response["score"] > 0

    def test_clients_interests(self):
        account = "test"
        login = "user"
        token = hashlib.sha512((account + login + "Otus").encode()).hexdigest()
        self.store = MockStore()
        self.store._data = {
            "i:1": '["books", "music"]',
            "i:2": '["sports"]'
        }
        request = {
            "account": account,
            "login": login,
            "method": "clients_interests",
            "token": token,
            "arguments": {
                "client_ids": [1, 2],
                "date": "01.01.2020"
            }
        }
        response, code = self.get_response(request)
        assert code == OK
        assert response[1] == ["books", "music"]
        assert response[2] == ["sports"]
