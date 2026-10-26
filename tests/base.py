import logging
import threading
import unittest

import requests
from werkzeug.serving import make_server

from app import create_app

logging.getLogger("werkzeug").setLevel(logging.ERROR)  # hide request logs


class ApiTestCase(unittest.TestCase):
    """Starts the real app on a free port, using the TEST database."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        # safety: never empty a database that is not clearly a test database
        assert "test" in cls.app.db.name.lower(), "Not a test database!"
        cls.server = make_server("127.0.0.1", 0, cls.app)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        # every test starts with an empty test database
        self.app.db.members.delete_many({})
        self.app.db.tasks.delete_many({})

    # --- helpers ---
    def post(self, path, body):
        return requests.post(self.base + path, json=body, timeout=5)

    def get(self, path, params=None):
        return requests.get(self.base + path, params=params, timeout=5)

    def put(self, path, body):
        return requests.put(self.base + path, json=body, timeout=5)

    def patch(self, path, body, actor_id=None):
        headers = {"X-Member-Id": actor_id} if actor_id else {}
        return requests.patch(self.base + path, json=body, headers=headers, timeout=5)

    def make_member(self, name="Asha", role="Developer"):
        return self.post("/members", {"name": name, "role": role}).json()

    def make_task(self, title="Fix login"):
        body = {"title": title, "description": "Some details", "priority": "High"}
        return self.post("/tasks", body).json()

    def assign(self, task, member_id):
        return self.put("/tasks/" + task["id"] + "/assignee", {"assignee_id": member_id})

    def set_status(self, task, status, actor_id=None):
        return self.patch("/tasks/" + task["id"] + "/status", {"status": status}, actor_id)

    def read_task(self, task):
        return self.get("/tasks/" + task["id"]).json()
