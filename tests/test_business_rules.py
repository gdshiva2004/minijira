from tests.base import ApiTestCase


class AssigneeRuleTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.dev = self.make_member("Dev", "Developer")
        self.qa = self.make_member("Quinn", "QA")
        self.task = self.make_task()

    def test_unassigned_task_cannot_move_to_in_progress(self):
        r = self.set_status(self.task, "In Progress", self.dev["id"])
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.read_task(self.task)["status"], "To Do")

    def test_unassigned_task_cannot_move_to_done(self):
        r = self.set_status(self.task, "Done", self.qa["id"])
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.read_task(self.task)["status"], "To Do")

    def test_assigned_task_can_move_to_in_progress(self):
        self.assign(self.task, self.dev["id"])
        r = self.set_status(self.task, "In Progress", self.dev["id"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.read_task(self.task)["status"], "In Progress")

    def test_task_unassigned_while_in_progress_cannot_be_signed_off(self):
        self.assign(self.task, self.dev["id"])
        self.set_status(self.task, "In Progress", self.dev["id"])
        self.assign(self.task, None)
        r = self.set_status(self.task, "Done", self.qa["id"])
        self.assertEqual(r.status_code, 409)

    def test_can_move_back_to_to_do(self):
        self.assign(self.task, self.dev["id"])
        self.set_status(self.task, "In Progress", self.dev["id"])
        r = self.set_status(self.task, "To Do", self.dev["id"])
        self.assertEqual(r.status_code, 200)

    def test_same_status_rejected(self):
        r = self.set_status(self.task, "To Do", self.dev["id"])
        self.assertEqual(r.status_code, 409)

    def test_invalid_status(self):
        r = self.set_status(self.task, "Blocked", self.dev["id"])
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_missing_status(self):
        r = self.patch("/tasks/" + self.task["id"] + "/status", {}, self.dev["id"])
        self.assertEqual(r.status_code, 400)

    def test_task_does_not_exist(self):
        r = self.patch("/tasks/" + "e" * 24 + "/status", {"status": "In Progress"}, self.dev["id"])
        self.assertEqual(r.status_code, 404)

    def test_bad_task_id(self):
        r = self.patch("/tasks/bad/status", {"status": "Done"}, self.dev["id"])
        self.assertEqual(r.status_code, 400)

    def test_errors_have_same_shape(self):
        for r in [self.set_status(self.task, "In Progress", self.dev["id"]),
                  self.set_status(self.task, "Nope", self.dev["id"]),
                  self.set_status(self.task, "Done")]:
            self.assertEqual(list(r.json().keys()), ["error"])


class QaSignOffTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.dev = self.make_member("Dev", "Developer")
        self.qa = self.make_member("Quinn", "QA")
        self.manager = self.make_member("Mia", "Manager")
        self.task = self.make_task()
        self.assign(self.task, self.dev["id"])
        self.set_status(self.task, "In Progress", self.dev["id"])

    def test_qa_can_mark_done(self):
        r = self.set_status(self.task, "Done", self.qa["id"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "Done")

    def test_developer_cannot_mark_done(self):
        self.assertEqual(self.set_status(self.task, "Done", self.dev["id"]).status_code, 403)

    def test_manager_cannot_mark_done(self):
        self.assertEqual(self.set_status(self.task, "Done", self.manager["id"]).status_code, 403)

    def test_rejected_sign_off_leaves_task_unchanged(self):
        self.set_status(self.task, "Done", self.dev["id"])
        self.assertEqual(self.read_task(self.task)["status"], "In Progress")

    def test_cannot_skip_in_progress(self):
        other = self.make_task("Other")
        self.assign(other, self.dev["id"])
        r = self.set_status(other, "Done", self.qa["id"])
        self.assertEqual(r.status_code, 409)

    def test_only_qa_check_applies_to_done_only(self):
        r = self.set_status(self.task, "To Do", self.dev["id"])
        self.assertEqual(r.status_code, 200)


class ActorTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.dev = self.make_member("Dev", "Developer")
        self.task = self.make_task()
        self.assign(self.task, self.dev["id"])

    def test_missing_header(self):
        self.assertEqual(self.set_status(self.task, "In Progress").status_code, 401)

    def test_malformed_header(self):
        self.assertEqual(self.set_status(self.task, "In Progress", "nope").status_code, 401)

    def test_unknown_member(self):
        self.assertEqual(self.set_status(self.task, "In Progress", "d" * 24).status_code, 401)

    def test_nothing_changes_without_actor(self):
        self.set_status(self.task, "In Progress")
        self.assertEqual(self.read_task(self.task)["status"], "To Do")


class AuditTrailTests(ApiTestCase):
    def test_new_task_has_no_history(self):
        task = self.make_task()
        self.assertIsNone(task["status_changed_by"])
        self.assertEqual(task["status_history"], [])

    def test_changes_are_recorded(self):
        dev = self.make_member("Dev", "Developer")
        qa = self.make_member("Quinn", "QA")
        task = self.make_task()
        self.assign(task, dev["id"])
        self.set_status(task, "In Progress", dev["id"])
        self.set_status(task, "Done", qa["id"])

        saved = self.read_task(task)
        self.assertEqual(saved["status_changed_by"], qa["id"])
        self.assertIsNotNone(saved["status_changed_at"])
        first, second = saved["status_history"]
        self.assertEqual((first["from"], first["to"], first["changed_by"]),
                         ("To Do", "In Progress", dev["id"]))
        self.assertEqual((second["from"], second["to"], second["changed_by"]),
                         ("In Progress", "Done", qa["id"]))
        self.assertIn("changed_at", first)

    def test_rejected_change_is_not_recorded(self):
        dev = self.make_member("Dev", "Developer")
        task = self.make_task()
        self.set_status(task, "In Progress", dev["id"])
        self.assertEqual(self.read_task(task)["status_history"], [])
