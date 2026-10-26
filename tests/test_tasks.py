from tests.base import ApiTestCase


class CreateTaskTests(ApiTestCase):
    def test_new_task_is_to_do_and_unassigned(self):
        body = {"title": "Fix bug", "description": "Details", "priority": "Medium"}
        r = self.post("/tasks", body)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "To Do")
        self.assertIsNone(r.json()["assignee_id"])

    def test_client_cannot_choose_status(self):
        body = {"title": "T", "description": "D", "priority": "Low", "status": "Done"}
        self.assertEqual(self.post("/tasks", body).json()["status"], "To Do")

    def test_missing_fields(self):
        full = {"title": "T", "description": "D", "priority": "Low"}
        for field in full:
            body = {k: v for k, v in full.items() if k != field}
            self.assertEqual(self.post("/tasks", body).status_code, 400)

    def test_blank_title(self):
        body = {"title": " ", "description": "D", "priority": "Low"}
        self.assertEqual(self.post("/tasks", body).status_code, 400)

    def test_invalid_priority(self):
        body = {"title": "T", "description": "D", "priority": "Urgent"}
        self.assertEqual(self.post("/tasks", body).status_code, 400)

    def test_get_task(self):
        task = self.make_task()
        r = self.get("/tasks/" + task["id"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Fix login")

    def test_get_task_bad_id(self):
        self.assertEqual(self.get("/tasks/abc").status_code, 400)

    def test_get_task_not_found(self):
        self.assertEqual(self.get("/tasks/" + "a" * 24).status_code, 404)


class FilterTaskTests(ApiTestCase):
    def test_list_all(self):
        self.make_task("One")
        self.make_task("Two")
        r = self.get("/tasks")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)

    def test_list_empty(self):
        self.assertEqual(self.get("/tasks").json(), [])

    def test_filter_by_status(self):
        member = self.make_member()
        one = self.make_task("One")
        self.make_task("Two")
        self.assign(one, member["id"])
        self.set_status(one, "In Progress", member["id"])

        in_progress = self.get("/tasks", {"status": "In Progress"}).json()
        to_do = self.get("/tasks", {"status": "To Do"}).json()
        self.assertEqual([t["title"] for t in in_progress], ["One"])
        self.assertEqual([t["title"] for t in to_do], ["Two"])

    def test_valid_status_with_no_matches(self):
        self.make_task()
        r = self.get("/tasks", {"status": "Done"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_invalid_status_rejected(self):
        self.assertEqual(self.get("/tasks", {"status": "Finished"}).status_code, 400)

    def test_empty_status_rejected(self):
        self.assertEqual(self.get("/tasks", {"status": ""}).status_code, 400)

    def test_status_filter_is_case_sensitive(self):
        self.assertEqual(self.get("/tasks", {"status": "to do"}).status_code, 400)


class OwnershipTests(ApiTestCase):
    def test_assign(self):
        task, member = self.make_task(), self.make_member()
        r = self.assign(task, member["id"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["assignee_id"], member["id"])

    def test_assignment_is_saved(self):
        task, member = self.make_task(), self.make_member()
        self.assign(task, member["id"])
        self.assertEqual(self.read_task(task)["assignee_id"], member["id"])

    def test_reassign(self):
        task = self.make_task()
        a, b = self.make_member("A"), self.make_member("B", "QA")
        self.assign(task, a["id"])
        r = self.assign(task, b["id"])
        self.assertEqual(r.json()["assignee_id"], b["id"])

    def test_unassign(self):
        task, member = self.make_task(), self.make_member()
        self.assign(task, member["id"])
        r = self.assign(task, None)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json()["assignee_id"])

    def test_member_does_not_exist(self):
        task, member = self.make_task(), self.make_member()
        self.assign(task, member["id"])
        r = self.assign(task, "b" * 24)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.read_task(task)["assignee_id"], member["id"])  # unchanged

    def test_bad_member_id(self):
        self.assertEqual(self.assign(self.make_task(), "xyz").status_code, 400)

    def test_task_does_not_exist(self):
        member = self.make_member()
        r = self.put("/tasks/" + "c" * 24 + "/assignee", {"assignee_id": member["id"]})
        self.assertEqual(r.status_code, 404)

    def test_bad_task_id(self):
        member = self.make_member()
        r = self.put("/tasks/bad/assignee", {"assignee_id": member["id"]})
        self.assertEqual(r.status_code, 400)

    def test_missing_assignee_field(self):
        r = self.put("/tasks/" + self.make_task()["id"] + "/assignee", {})
        self.assertEqual(r.status_code, 400)
