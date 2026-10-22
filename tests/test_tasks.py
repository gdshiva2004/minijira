import requests

from tests.base import ApiTestCase


class TaskCreationTests(ApiTestCase):
    def test_create_task_success_defaults_to_todo(self):
        r = requests.post(
            self.url("/tasks"),
            json={"title": "Fix bug", "description": "Details", "priority": "Medium"},
            timeout=5,
        )
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["status"], "To Do")
        self.assertIsNone(body["assignee_id"])
        self.assertEqual(body["priority"], "Medium")

    def test_client_cannot_set_status_on_create(self):
        r = requests.post(
            self.url("/tasks"),
            json={"title": "T", "description": "D", "priority": "Low", "status": "Done"},
            timeout=5,
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "To Do")

    def test_missing_fields(self):
        base = {"title": "T", "description": "D", "priority": "Low"}
        for field in base:
            body = {k: v for k, v in base.items() if k != field}
            r = requests.post(self.url("/tasks"), json=body, timeout=5)
            self.assertEqual(r.status_code, 400, field)

    def test_blank_title(self):
        r = requests.post(
            self.url("/tasks"),
            json={"title": " ", "description": "D", "priority": "Low"},
            timeout=5,
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_priority(self):
        r = requests.post(
            self.url("/tasks"),
            json={"title": "T", "description": "D", "priority": "Urgent"},
            timeout=5,
        )
        self.assertEqual(r.status_code, 400)

    def test_title_too_long(self):
        r = requests.post(
            self.url("/tasks"),
            json={"title": "x" * 201, "description": "D", "priority": "Low"},
            timeout=5,
        )
        self.assertEqual(r.status_code, 400)

    def test_get_task_by_id(self):
        task = self.make_task()
        r = requests.get(self.url(f"/tasks/{task['id']}"), timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], task["id"])

    def test_get_task_invalid_id(self):
        r = requests.get(self.url("/tasks/not-an-id"), timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_get_task_not_found(self):
        r = requests.get(self.url("/tasks/" + "a" * 24), timeout=5)
        self.assertEqual(r.status_code, 404)


class TaskDiscoveryTests(ApiTestCase):
    def test_list_all_tasks(self):
        self.make_task("One")
        self.make_task("Two")
        r = requests.get(self.url("/tasks"), timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([t["title"] for t in r.json()], ["One", "Two"])

    def test_list_empty(self):
        r = requests.get(self.url("/tasks"), timeout=5)
        self.assertEqual(r.json(), [])

    def test_filter_by_status_todo(self):
        self.make_task("One")
        r = requests.get(self.url("/tasks"), params={"status": "To Do"}, timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_filter_returns_only_matching(self):
        # Day 6 adds the status endpoint; until then, set status directly in the test DB.
        t1 = self.make_task("One")
        self.make_task("Two")
        from bson import ObjectId

        self.db.tasks.update_one({"_id": ObjectId(t1["id"])}, {"$set": {"status": "In Progress"}})
        r = requests.get(self.url("/tasks"), params={"status": "In Progress"}, timeout=5)
        self.assertEqual([t["title"] for t in r.json()], ["One"])
        r = requests.get(self.url("/tasks"), params={"status": "To Do"}, timeout=5)
        self.assertEqual([t["title"] for t in r.json()], ["Two"])

    def test_filter_valid_status_no_matches(self):
        self.make_task("One")
        r = requests.get(self.url("/tasks"), params={"status": "Done"}, timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_invalid_status_filter_rejected(self):
        r = requests.get(self.url("/tasks"), params={"status": "Finished"}, timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_empty_status_filter_rejected(self):
        r = requests.get(self.url("/tasks"), params={"status": ""}, timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_status_filter_is_case_sensitive(self):
        r = requests.get(self.url("/tasks"), params={"status": "to do"}, timeout=5)
        self.assertEqual(r.status_code, 400)


class TaskOwnershipTests(ApiTestCase):
    def assign(self, task_id, payload):
        return requests.put(self.url(f"/tasks/{task_id}/assignee"), json=payload, timeout=5)

    def test_new_task_is_unassigned(self):
        self.assertIsNone(self.make_task()["assignee_id"])

    def test_assign_task(self):
        task, member = self.make_task(), self.make_member()
        r = self.assign(task["id"], {"assignee_id": member["id"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["assignee_id"], member["id"])

    def test_assignment_persists(self):
        task, member = self.make_task(), self.make_member()
        self.assign(task["id"], {"assignee_id": member["id"]})
        r = requests.get(self.url(f"/tasks/{task['id']}"), timeout=5)
        self.assertEqual(r.json()["assignee_id"], member["id"])

    def test_reassign_task(self):
        task = self.make_task()
        a, b = self.make_member("A"), self.make_member("B", "QA")
        self.assign(task["id"], {"assignee_id": a["id"]})
        r = self.assign(task["id"], {"assignee_id": b["id"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["assignee_id"], b["id"])

    def test_unassign_task(self):
        task, member = self.make_task(), self.make_member()
        self.assign(task["id"], {"assignee_id": member["id"]})
        r = self.assign(task["id"], {"assignee_id": None})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json()["assignee_id"])

    def test_nonexistent_member_rejected_and_task_unchanged(self):
        task, member = self.make_task(), self.make_member()
        self.assign(task["id"], {"assignee_id": member["id"]})
        r = self.assign(task["id"], {"assignee_id": "b" * 24})
        self.assertEqual(r.status_code, 404)
        after = requests.get(self.url(f"/tasks/{task['id']}"), timeout=5).json()
        self.assertEqual(after["assignee_id"], member["id"])

    def test_invalid_member_id_format(self):
        task = self.make_task()
        r = self.assign(task["id"], {"assignee_id": "xyz"})
        self.assertEqual(r.status_code, 400)

    def test_non_string_member_id(self):
        task = self.make_task()
        r = self.assign(task["id"], {"assignee_id": 5})
        self.assertEqual(r.status_code, 400)

    def test_nonexistent_task(self):
        member = self.make_member()
        r = self.assign("c" * 24, {"assignee_id": member["id"]})
        self.assertEqual(r.status_code, 404)

    def test_invalid_task_id_format(self):
        member = self.make_member()
        r = self.assign("bad-id", {"assignee_id": member["id"]})
        self.assertEqual(r.status_code, 400)

    def test_missing_assignee_field(self):
        task = self.make_task()
        r = self.assign(task["id"], {})
        self.assertEqual(r.status_code, 400)
