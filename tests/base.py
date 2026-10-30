import logging
import threading
import unittest

import requests
from werkzeug.serving import make_server

from app import create_app
from app.config import DB_NAME

logging.getLogger("werkzeug").setLevel(logging.ERROR)

PASSWORD = "password123"
ANONYMOUS = "anonymous"


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        assert "test" in cls.app.db.name.lower(), "Not a test database!"
        assert cls.app.db.name != DB_NAME, "TEST_DB_NAME must differ from DB_NAME"
        cls.server = make_server("127.0.0.1", 0, cls.app)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        self.app.db.members.delete_many({})
        self.app.db.tasks.delete_many({})
        self.counter = 0
        self.admin = self.make_member("Admin", "Manager")

    def headers(self, who):
        if who == ANONYMOUS:
            return {}
        member = who or self.admin
        return {"Authorization": "Bearer " + member["token"]}

    def post(self, path, body, who=None):
        return requests.post(self.base + path, json=body, headers=self.headers(who), timeout=5)

    def get(self, path, params=None, who=None):
        return requests.get(self.base + path, params=params, headers=self.headers(who), timeout=5)

    def put(self, path, body, who=None):
        return requests.put(self.base + path, json=body, headers=self.headers(who), timeout=5)

    def patch(self, path, body, who=None):
        return requests.patch(self.base + path, json=body, headers=self.headers(who), timeout=5)

    def signup(self, **fields):
        return requests.post(self.base + "/auth/signup", json=fields, timeout=5)

    def login(self, email, password=PASSWORD):
        return requests.post(
            self.base + "/auth/login", json={"email": email, "password": password}, timeout=5
        )

    def make_member(self, name="Asha", role="Developer"):
        self.counter += 1
        email = "user%d@example.com" % self.counter
        r = self.signup(name=name, email=email, password=PASSWORD, role=role)
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        member = body["member"]
        member["token"] = body["token"]
        return member

    def make_task(self, title="Fix login", who=None):
        body = {"title": title, "description": "Some details", "priority": "High"}
        return self.post("/tasks", body, who).json()

    def assign(self, task, member_id, who=None):
        return self.put("/tasks/" + task["id"] + "/assignee", {"assignee_id": member_id}, who)

    def set_status(self, task, status, who=None):
        return self.patch("/tasks/" + task["id"] + "/status", {"status": status}, who)

    def read_task(self, task):
        return self.get("/tasks/" + task["id"]).json()
