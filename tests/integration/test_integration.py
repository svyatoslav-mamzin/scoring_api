import os
import json
import unittest
from time import sleep
from store import Store
from threading import Thread
from api import MainHTTPHandler
from constants import HOST, PORT
from tests.unit.test import cases
from http.server import HTTPServer
from http.client import HTTPConnection


TEST_HOST = os.environ.get("TEST_HOST", None)
TEST_PORT = os.environ.get("TEST_PORT", None)
TEST_REDIS_HOST = os.environ.get("TEST_REDIS_HOST", HOST)
TEST_REDIS_PORT = os.environ.get("TEST_REDIS_PORT", PORT)


class TestHTTP(unittest.TestCase):
    host = TEST_HOST
    port = TEST_PORT

    headers = {"Content-type": "application/json",
               "Accept": "text/plain"}

    server = None
    thread = None

    @classmethod
    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def setUpClass(cls):
        cls.server = HTTPServer((cls.host, cls.port), MainHTTPHandler)
        cls.thread = Thread(target=cls.server.serve_forever)
        cls.thread.start()

    @classmethod
    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()

    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def setUp(self):
        self.conn = HTTPConnection(self.host, self.port, timeout=10)

    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def tearDown(self):
        self.conn.close()

    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def test_online_score(self):
        req = {"account": "horns&hoofs",
               "login": "h&f",
               "method": "online_score",
               "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
               "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав",
                             "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}
        self.conn.request("POST", "/method/", json.dumps(req), self.headers)
        r = self.conn.getresponse()
        data = json.load(r)
        response = data['response']
        self.assertEqual(r.status, 200)
        self.assertIn('score', response)
        self.assertEqual(response['score'], '5.0')

    @cases([{"account": "horns&hoofs",  # empty token
               "login": "h&f",
               "method": "online_score",
               "token": "",
               "arguments": {}},
            {"account": "horns&hoofs",  # invalid token
             "login": "h&f",
             "method": "online_score",
             "token": "sdd",
             "arguments": {}},
            {"account": "horns&hoof",  # broken acc
             "login": "h&f",
             "method": "online_score",
             "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
             "arguments": {}},
            {"account": "",  # empty acc
             "login": "h&f",
             "method": "online_score",
             "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
             "arguments": {}},
            {"account": "horns&hoofs",  # broken login
             "login": "h&",
             "method": "online_score",
             "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
             "arguments": {}},
            {"account": "horns&hoofs",  # empty login
             "login": "",
             "method": "online_score",
             "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
             "arguments": {}},
            {"account": "",
             "login": "",
             "method": "online_score",
             "token": "",
             "arguments": {}},
            {"account": "horns&hoofs",
             "login": "",
             "method": "online_score",
             "token": "",
             "arguments": {}},
            ])
    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def test_bad_auth(self, request):
        self.conn.request("POST", "/method/", json.dumps(request), self.headers)
        r = self.conn.getresponse()
        data = json.load(r)
        self.assertIn('error', data)
        self.assertEqual(r.status, 403)
        self.assertEqual(data['error'], 'Forbidden')

    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def test_unexpected_method(self):
        self.conn.request("GET", "/method/")
        r = self.conn.getresponse()
        data = r.read()
        self.assertEqual(r.status, 501)

    @cases(["/me/", "/", "../../"])
    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def test_unexpected_url(self, url):
        req = {"account": "horns&hoofs",
               "login": "h&f",
               "method": "online_score",
               "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
               "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав",
                             "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}
        self.conn.request("POST", url, json.dumps(req), self.headers)
        r = self.conn.getresponse()
        data = json.load(r)
        self.assertIn('error', data)
        self.assertEqual(r.status, 404)

    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def test_unexpected_api_method(self):
        req = {"account": "horns&hoofs",
               "login": "h&f",
               "method": "foo",
               "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
               "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав",
                             "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}
        self.conn.request("POST", "method", json.dumps(req), self.headers)
        r = self.conn.getresponse()
        data = json.load(r)
        self.assertIn('error', data)
        self.assertEqual(r.status, 405)

    @unittest.skipIf(TEST_HOST is None or TEST_PORT is None, "The test host and port are not specified")
    def test_clients_interests(self):
        req = {"account": "horns&hoofs",
               "login": "h&f",
               "method": "clients_interests",
               "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
               "arguments": {"client_ids": [1, 2, 3, 4], "date": "20.07.2017"}}
        self.conn.request("POST", "/method/", json.dumps(req), self.headers)
        r = self.conn.getresponse()
        data = json.load(r)
        self.assertIn('response', data)
        response = data['response']
        self.assertEqual(type(response), dict)
        for key, value in response.items():
            self.assertEqual(type(key), str)
            self.assertEqual(type(value), list)


class TestStore(unittest.TestCase):
    store = Store()

    @unittest.skipIf(TEST_REDIS_HOST is None or TEST_REDIS_PORT is None, "The test host and port are not specified")
    def test_cache_set(self):
        self.assertTrue(self.store.cache_set('key1', 'value1'))

    @unittest.skipIf(TEST_REDIS_HOST is None or TEST_REDIS_PORT is None, "The test host and port are not specified")
    def test_cache_get(self):
        self.store.cache_set('key2', 'value2')
        value = self.store.cache_get('key2')
        self.assertEqual(value, 'value2')

    @unittest.skipIf(TEST_REDIS_HOST is None or TEST_REDIS_PORT is None, "The test host and port are not specified")
    def test_cache_timeout(self):
        self.store.cache_set('key3', 'value3', cache_time=2)
        sleep(2)
        value = self.store.cache_get('key3')
        self.assertEqual(value, None)

    @unittest.skipIf(TEST_REDIS_HOST is None or TEST_REDIS_PORT is None, "The test host and port are not specified")
    def test_set(self):
        self.assertTrue(self.store.set('key4', 'value4'))

    @unittest.skipIf(TEST_REDIS_HOST is None or TEST_REDIS_PORT is None, "The test host and port are not specified")
    def test_get(self):
        self.store.set('key5', 'value5')
        value = self.store.get('key5')
        self.assertEqual(value, 'value5')

    @unittest.skipIf(TEST_REDIS_HOST is None or TEST_REDIS_PORT is None, "The test host and port are not specified")
    def test_reconnect(self):
        class FakeRedis:
            attempts = 3
            @classmethod
            def get(cls, key):
                cls.attempts -= 1
                if not cls.attempts == 0:
                    raise Exception
                return key
        tmp_store = self.store.store
        self.store.store = FakeRedis()
        value = self.store.get('key6')
        self.assertEqual(value, 'key6')
        self.store.store = tmp_store


if __name__ == "__main__":
    unittest.main()
