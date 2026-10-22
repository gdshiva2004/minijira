import requests

from tests.base import ApiTestCase


class HealthTests(ApiTestCase):
    def test_health(self):
        r = requests.get(self.url("/health"), timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})

    def test_health_db(self):
        r = requests.get(self.url("/health/db"), timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["database"], "connected")


class MemberTests(ApiTestCase):
    def test_create_member_success(self):
        r = requests.post(self.url("/members"), json={"name": " Asha ", "role": "QA"}, timeout=5)
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["name"], "Asha")  # trimmed
        self.assertEqual(body["role"], "QA")
        self.assertIn("id", body)

    def test_all_roles_accepted(self):
        for role in ("Developer", "QA", "Manager"):
            self.assertEqual(self.make_member(role=role)["role"], role)

    def test_missing_name(self):
        r = requests.post(self.url("/members"), json={"role": "QA"}, timeout=5)
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_blank_name(self):
        r = requests.post(self.url("/members"), json={"name": "   ", "role": "QA"}, timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_non_string_name(self):
        r = requests.post(self.url("/members"), json={"name": 123, "role": "QA"}, timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_invalid_role(self):
        r = requests.post(self.url("/members"), json={"name": "Bob", "role": "CEO"}, timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_missing_role(self):
        r = requests.post(self.url("/members"), json={"name": "Bob"}, timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_body_not_json(self):
        r = requests.post(self.url("/members"), data="not json", timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_body_not_object(self):
        r = requests.post(self.url("/members"), json=["a"], timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_list_members(self):
        self.make_member("Asha", "Developer")
        self.make_member("Ravi", "QA")
        r = requests.get(self.url("/members"), timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m["name"] for m in r.json()], ["Asha", "Ravi"])

    def test_list_members_empty(self):
        r = requests.get(self.url("/members"), timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])
