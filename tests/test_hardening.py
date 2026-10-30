from unittest.mock import patch

from bson import ObjectId
from pymongo.errors import PyMongoError

from tests.base import ApiTestCase


class InputLimitTests(ApiTestCase):
    def test_name_too_long(self):
        r = self.post("/members", {"name": "x" * 101, "role": "QA"})
        self.assertEqual(r.status_code, 400)

    def test_name_at_limit_is_ok(self):
        r = self.post("/members", {"name": "x" * 100, "role": "QA"})
        self.assertEqual(r.status_code, 201)

    def test_title_too_long(self):
        r = self.post("/tasks", {"title": "x" * 201, "description": "d", "priority": "Low"})
        self.assertEqual(r.status_code, 400)

    def test_description_too_long(self):
        r = self.post("/tasks", {"title": "t", "description": "x" * 2001, "priority": "Low"})
        self.assertEqual(r.status_code, 400)


class ErrorShapeTests(ApiTestCase):
    def test_unknown_url_is_json(self):
        r = self.get("/nope")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(list(r.json().keys()), ["error"])

    def test_wrong_method_is_json(self):
        r = self.put("/members", {})
        self.assertEqual(r.status_code, 405)
        self.assertEqual(list(r.json().keys()), ["error"])

    def test_database_failure_gives_503_json(self):
        with patch("app.routes.get_db") as fake_get_db:
            fake_get_db.return_value.members.find.side_effect = PyMongoError("down")
            r = self.get("/members")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(list(r.json().keys()), ["error"])


class OldDataTests(ApiTestCase):
    def test_task_saved_without_newer_fields_still_loads(self):
        old = {"title": "old", "description": "d", "priority": "Low",
               "status": "To Do", "assignee_id": None}
        task_id = self.app.db.tasks.insert_one(old).inserted_id
        r = self.get("/tasks/" + str(task_id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status_history"], [])
        self.assertEqual(self.get("/tasks").status_code, 200)


class OrderingTests(ApiTestCase):
    def test_lists_are_oldest_first(self):
        for name in ["A", "B", "C"]:
            self.make_member(name)
            self.make_task(name)
        self.assertEqual([m["name"] for m in self.get("/members").json()], ["A", "B", "C"])
        self.assertEqual([t["title"] for t in self.get("/tasks").json()], ["A", "B", "C"])


class ConcurrentChangeTests(ApiTestCase):
    def test_stale_status_change_is_rejected(self):
        dev = self.make_member("Dev", "Developer")
        task = self.make_task()
        self.assign(task, dev["id"])
        stale = self.app.db.tasks.find_one({"_id": ObjectId(task["id"])})
        self.set_status(task, "In Progress", dev["id"])

        with patch("app.routes.find_task", return_value=(stale, None)):
            r = self.set_status(task, "In Progress", dev["id"])

        self.assertEqual(r.status_code, 409)
        saved = self.read_task(task)
        self.assertEqual(len(saved["status_history"]), 1)
