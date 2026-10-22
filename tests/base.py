import logging
import threading
import unittest

import requests
from werkzeug.serving import make_server

from app import create_app
from app.config import TestConfig


logging.getLogger("werkzeug").setLevel(logging.ERROR)  # quiet request logs


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)
        # Safety: never wipe a database that is not clearly a test database.
        assert "test" in cls.app.config["DB_NAME"].lower(), "Refusing to use a non-test DB"
        cls.db = cls.app.extensions["mongo_db"]
        cls.server = make_server("127.0.0.1", 0, cls.app)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.app.extensions["mongo_client"].close()

    def setUp(self):
        self.db.members.delete_many({})
        self.db.tasks.delete_many({})

    def url(self, path):
        return self.base_url + path

    def make_member(self, name="Asha", role="Developer"):
        r = requests.post(self.url("/members"), json={"name": name, "role": role}, timeout=5)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def make_task(self, title="Fix login", description="Login page crashes", priority="High"):
        r = requests.post(
            self.url("/tasks"),
            json={"title": title, "description": description, "priority": priority},
            timeout=5,
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()
