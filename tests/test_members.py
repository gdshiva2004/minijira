from bson import ObjectId

from tests.base import ANONYMOUS, ApiTestCase


class MemberTests(ApiTestCase):
    def test_health(self):
        self.assertEqual(self.get("/health", who=ANONYMOUS).status_code, 200)
        self.assertEqual(self.get("/health/db", who=ANONYMOUS).status_code, 200)

    def test_list_members(self):
        self.make_member("Asha", "Developer")
        self.make_member("Ravi", "QA")
        r = self.get("/members")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m["name"] for m in r.json()], ["Admin", "Asha", "Ravi"])

    def test_list_shows_roles(self):
        self.make_member("Ravi", "QA")
        roles = [m["role"] for m in self.get("/members").json()]
        self.assertEqual(roles, ["Manager", "QA"])

    def test_list_never_exposes_passwords(self):
        self.make_member("Asha")
        for member in self.get("/members").json():
            self.assertNotIn("password", member)
            self.assertNotIn("password_hash", member)
        self.assertNotIn("password", self.get("/members").text.lower())

    def test_all_three_roles_can_be_created(self):
        for role in ["Developer", "QA", "Manager"]:
            self.assertEqual(self.make_member("A", role)["role"], role)

    def test_old_member_without_login_still_listed(self):
        self.app.db.members.insert_one({"name": "Legacy", "role": "QA"})
        names = [m["name"] for m in self.get("/members").json()]
        self.assertIn("Legacy", names)

    def test_members_require_login(self):
        self.assertEqual(self.get("/members", who=ANONYMOUS).status_code, 401)

    def test_member_ids_are_valid_object_ids(self):
        member = self.make_member()
        ObjectId(member["id"])
