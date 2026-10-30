from tests.base import ApiTestCase


class MemberTests(ApiTestCase):
    def test_health(self):
        self.assertEqual(self.get("/health").status_code, 200)
        self.assertEqual(self.get("/health/db").status_code, 200)

    def test_create_member(self):
        r = self.post("/members", {"name": "Asha", "role": "QA"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["name"], "Asha")
        self.assertEqual(r.json()["role"], "QA")

    def test_name_is_trimmed(self):
        r = self.post("/members", {"name": "  Asha  ", "role": "QA"})
        self.assertEqual(r.json()["name"], "Asha")

    def test_all_roles_work(self):
        for role in ["Developer", "QA", "Manager"]:
            self.assertEqual(self.post("/members", {"name": "A", "role": role}).status_code, 201)

    def test_missing_name(self):
        self.assertEqual(self.post("/members", {"role": "QA"}).status_code, 400)

    def test_blank_name(self):
        self.assertEqual(self.post("/members", {"name": "  ", "role": "QA"}).status_code, 400)

    def test_name_not_a_string(self):
        self.assertEqual(self.post("/members", {"name": 5, "role": "QA"}).status_code, 400)

    def test_invalid_role(self):
        self.assertEqual(self.post("/members", {"name": "A", "role": "CEO"}).status_code, 400)

    def test_missing_role(self):
        self.assertEqual(self.post("/members", {"name": "A"}).status_code, 400)

    def test_body_is_not_json(self):
        self.assertEqual(self.post("/members", None).status_code, 400)

    def test_list_members(self):
        self.make_member("Asha", "Developer")
        self.make_member("Ravi", "QA")
        r = self.get("/members")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m["name"] for m in r.json()], ["Asha", "Ravi"])

    def test_list_members_empty(self):
        self.assertEqual(self.get("/members").json(), [])
