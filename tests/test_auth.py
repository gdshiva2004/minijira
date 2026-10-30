import base64
import json
from datetime import datetime, timedelta, timezone

import jwt
import requests
from bson import ObjectId

from tests.base import ANONYMOUS, PASSWORD, ApiTestCase


def valid_fields(**changes):
    fields = {"name": "Asha", "email": "asha@example.com", "password": PASSWORD, "role": "Developer"}
    fields.update(changes)
    return fields


class SignupTests(ApiTestCase):
    def test_signup_success(self):
        r = self.signup(**valid_fields())
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertTrue(body["token"])
        self.assertEqual(body["member"]["name"], "Asha")
        self.assertEqual(body["member"]["email"], "asha@example.com")
        self.assertEqual(body["member"]["role"], "Developer")
        self.assertIn("id", body["member"])

    def test_signup_response_has_no_password(self):
        r = self.signup(**valid_fields())
        self.assertNotIn("password", r.text.lower())

    def test_password_is_stored_hashed(self):
        self.signup(**valid_fields())
        saved = self.app.db.members.find_one({"email": "asha@example.com"})
        self.assertNotEqual(saved["password_hash"], PASSWORD)
        self.assertNotIn(PASSWORD, saved["password_hash"])
        self.assertNotIn("password", saved)

    def test_email_is_trimmed_and_lowercased(self):
        r = self.signup(**valid_fields(email="  Asha@Example.COM "))
        self.assertEqual(r.json()["member"]["email"], "asha@example.com")

    def test_name_is_trimmed(self):
        r = self.signup(**valid_fields(name="  Asha  "))
        self.assertEqual(r.json()["member"]["name"], "Asha")

    def test_every_role_can_sign_up(self):
        for i, role in enumerate(["Developer", "QA", "Manager"]):
            r = self.signup(**valid_fields(email="r%d@example.com" % i, role=role))
            self.assertEqual(r.status_code, 201)

    def test_missing_name(self):
        fields = valid_fields()
        del fields["name"]
        self.assertEqual(self.signup(**fields).status_code, 400)

    def test_blank_name(self):
        self.assertEqual(self.signup(**valid_fields(name="   ")).status_code, 400)

    def test_name_not_a_string(self):
        self.assertEqual(self.signup(**valid_fields(name=5)).status_code, 400)

    def test_name_too_long(self):
        self.assertEqual(self.signup(**valid_fields(name="x" * 101)).status_code, 400)

    def test_invalid_emails(self):
        for email in ["", "plain", "a@b", "a b@c.com", "@c.com", "a@@c.com", 5, None]:
            r = self.signup(**valid_fields(email=email))
            self.assertEqual(r.status_code, 400, repr(email))

    def test_missing_email(self):
        fields = valid_fields()
        del fields["email"]
        self.assertEqual(self.signup(**fields).status_code, 400)

    def test_password_too_short(self):
        self.assertEqual(self.signup(**valid_fields(password="short")).status_code, 400)

    def test_password_too_long(self):
        self.assertEqual(self.signup(**valid_fields(password="x" * 129)).status_code, 400)

    def test_password_missing_or_not_text(self):
        fields = valid_fields()
        del fields["password"]
        self.assertEqual(self.signup(**fields).status_code, 400)
        self.assertEqual(self.signup(**valid_fields(password=12345678)).status_code, 400)

    def test_invalid_role(self):
        self.assertEqual(self.signup(**valid_fields(role="CEO")).status_code, 400)

    def test_missing_role(self):
        fields = valid_fields()
        del fields["role"]
        self.assertEqual(self.signup(**fields).status_code, 400)

    def test_body_is_not_json(self):
        r = self.post("/auth/signup", None, ANONYMOUS)
        self.assertEqual(r.status_code, 400)

    def test_duplicate_email_rejected(self):
        self.assertEqual(self.signup(**valid_fields()).status_code, 201)
        r = self.signup(**valid_fields(name="Someone Else"))
        self.assertEqual(r.status_code, 409)
        self.assertIn("error", r.json())

    def test_duplicate_email_ignores_case(self):
        self.signup(**valid_fields())
        r = self.signup(**valid_fields(email="ASHA@EXAMPLE.COM"))
        self.assertEqual(r.status_code, 409)

    def test_failed_signup_creates_nothing(self):
        before = len(self.get("/members").json())
        self.signup(**valid_fields(password="short"))
        self.assertEqual(len(self.get("/members").json()), before)


class LoginTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.signup(**valid_fields())

    def test_login_success(self):
        r = self.login("asha@example.com")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["token"])
        self.assertEqual(r.json()["member"]["email"], "asha@example.com")

    def test_login_email_ignores_case_and_spaces(self):
        self.assertEqual(self.login("  ASHA@example.com ").status_code, 200)

    def test_login_response_has_no_password(self):
        self.assertNotIn("password", self.login("asha@example.com").text.lower())

    def test_wrong_password(self):
        r = self.login("asha@example.com", "wrong-password")
        self.assertEqual(r.status_code, 401)
        self.assertIn("error", r.json())

    def test_unknown_email(self):
        self.assertEqual(self.login("nobody@example.com").status_code, 401)

    def test_same_message_for_wrong_password_and_unknown_email(self):
        wrong = self.login("asha@example.com", "wrong-password").json()
        unknown = self.login("nobody@example.com").json()
        self.assertEqual(wrong, unknown)

    def test_missing_fields(self):
        for body in [{}, {"email": "asha@example.com"}, {"password": PASSWORD},
                     {"email": "asha@example.com", "password": ""}, {"email": "bad", "password": "x"}]:
            r = self.post("/auth/login", body, ANONYMOUS)
            self.assertEqual(r.status_code, 400, body)

    def test_body_is_not_json(self):
        self.assertEqual(self.post("/auth/login", None, ANONYMOUS).status_code, 400)

    def test_member_without_password_cannot_log_in(self):
        self.app.db.members.insert_one({"name": "Old", "role": "QA", "email": "old@example.com"})
        self.assertEqual(self.login("old@example.com").status_code, 401)

    def test_token_from_login_works(self):
        token = self.login("asha@example.com").json()["token"]
        r = self.get("/auth/me", who={"token": token})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["email"], "asha@example.com")


class TokenTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.member = self.make_member("Asha", "Developer")
        self.secret = self.app.config["JWT_SECRET"]

    def encode(self, payload, secret=None, algorithm="HS256"):
        return jwt.encode(payload, secret or self.secret, algorithm=algorithm)

    def payload(self, **changes):
        data = {
            "sub": self.member["id"],
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        data.update(changes)
        return data

    def status_with(self, token):
        return self.get("/auth/me", who={"token": token}).status_code

    def test_me_returns_current_member(self):
        r = self.get("/auth/me", who=self.member)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], self.member["id"])
        self.assertNotIn("password_hash", r.json())

    def test_token_contains_expiry_and_subject(self):
        data = jwt.decode(self.member["token"], self.secret, algorithms=["HS256"])
        self.assertEqual(data["sub"], self.member["id"])
        self.assertGreater(data["exp"], data["iat"])

    def test_token_lifetime_matches_setting(self):
        data = jwt.decode(self.member["token"], self.secret, algorithms=["HS256"])
        minutes = (data["exp"] - data["iat"]) / 60
        self.assertEqual(minutes, self.app.config["JWT_EXPIRES_MINUTES"])

    def test_valid_handmade_token_works(self):
        self.assertEqual(self.status_with(self.encode(self.payload())), 200)

    def test_expired_token(self):
        expired = self.payload(exp=datetime.now(timezone.utc) - timedelta(minutes=1))
        r = self.get("/auth/me", who={"token": self.encode(expired)})
        self.assertEqual(r.status_code, 401)
        self.assertIn("expired", r.json()["error"].lower())

    def test_token_signed_with_wrong_secret(self):
        token = self.encode(self.payload(), secret="another-secret-that-is-long-enough-123456")
        self.assertEqual(self.status_with(token), 401)

    def test_unsigned_token_rejected(self):
        token = jwt.encode(self.payload(), None, algorithm="none")
        self.assertEqual(self.status_with(token), 401)

    def test_tampered_payload_rejected(self):
        other = self.make_member("Other", "QA")
        header, _, signature = self.member["token"].split(".")
        forged = json.dumps({"sub": other["id"], "exp": 4102444800}).encode()
        payload = base64.urlsafe_b64encode(forged).rstrip(b"=").decode()
        self.assertEqual(self.status_with(header + "." + payload + "." + signature), 401)

    def test_token_without_expiry_rejected(self):
        payload = self.payload()
        del payload["exp"]
        self.assertEqual(self.status_with(self.encode(payload)), 401)

    def test_token_without_subject_rejected(self):
        payload = self.payload()
        del payload["sub"]
        self.assertEqual(self.status_with(self.encode(payload)), 401)

    def test_token_for_unknown_account_rejected(self):
        token = self.encode(self.payload(sub=str(ObjectId())))
        self.assertEqual(self.status_with(token), 401)

    def test_token_with_invalid_subject_rejected(self):
        self.assertEqual(self.status_with(self.encode(self.payload(sub="not-an-id"))), 401)

    def test_garbage_token(self):
        self.assertEqual(self.status_with("not.a.token"), 401)
        self.assertEqual(self.status_with("garbage"), 401)

    def test_deleted_account_token_stops_working(self):
        self.app.db.members.delete_many({"_id": ObjectId(self.member["id"])})
        self.assertEqual(self.get("/auth/me", who=self.member).status_code, 401)

    def test_missing_authorization_header(self):
        self.assertEqual(self.get("/auth/me", who=ANONYMOUS).status_code, 401)

    def test_wrong_scheme_rejected(self):
        r = requests.get(self.base + "/auth/me", headers={"Authorization": "Token " + self.member["token"]}, timeout=5)
        self.assertEqual(r.status_code, 401)

    def test_bearer_without_token_rejected(self):
        r = requests.get(self.base + "/auth/me", headers={"Authorization": "Bearer "}, timeout=5)
        self.assertEqual(r.status_code, 401)

    def test_unauthorized_response_asks_for_bearer(self):
        r = self.get("/auth/me", who=ANONYMOUS)
        self.assertEqual(r.headers.get("WWW-Authenticate"), "Bearer")
        self.assertEqual(list(r.json().keys()), ["error"])


class ProtectedEndpointTests(ApiTestCase):
    def test_every_endpoint_requires_login(self):
        task = self.make_task()
        some_id = "a" * 24
        calls = [
            ("get", "/members", None),
            ("get", "/tasks", None),
            ("get", "/tasks/" + task["id"], None),
            ("post", "/tasks", {"title": "T", "description": "D", "priority": "Low"}),
            ("put", "/tasks/" + task["id"] + "/assignee", {"assignee_id": None}),
            ("patch", "/tasks/" + task["id"] + "/status", {"status": "In Progress"}),
            ("get", "/auth/me", None),
            ("get", "/tasks/" + some_id, None),
        ]
        for method, path, body in calls:
            if method == "get":
                r = self.get(path, who=ANONYMOUS)
            else:
                r = getattr(self, method)(path, body, ANONYMOUS)
            self.assertEqual(r.status_code, 401, method + " " + path)

    def test_health_stays_public(self):
        self.assertEqual(self.get("/health", who=ANONYMOUS).status_code, 200)

    def test_signup_and_login_stay_public(self):
        self.assertEqual(self.post("/auth/signup", {}, ANONYMOUS).status_code, 400)
        self.assertEqual(self.post("/auth/login", {}, ANONYMOUS).status_code, 400)

    def test_blocked_request_changes_nothing(self):
        task = self.make_task()
        self.patch("/tasks/" + task["id"] + "/status", {"status": "In Progress"}, ANONYMOUS)
        self.assertEqual(self.read_task(task)["status"], "To Do")
