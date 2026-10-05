from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

User = get_user_model()
PASSWORD = "Str0ng!Pass#42"


class AuthTests(APITestCase):
    def setUp(self):
        cache.clear()  # reset throttling counters between tests
        self.payload = {
            "username": "alice", "email": "alice@example.com",
            "password": PASSWORD, "password2": PASSWORD,
        }

    def login(self, username="alice", password=PASSWORD):
        return self.client.post(
            "/api/auth/login/", {"username": username, "password": password}, format="json"
        )

    def test_register_hashes_password(self):
        r = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("password", r.data)
        user = User.objects.get(username="alice")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password(PASSWORD))

    def test_register_password_mismatch(self):
        self.payload["password2"] = "different"
        r = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(r.status_code, 400)

    def test_register_weak_password(self):
        self.payload["password"] = self.payload["password2"] = "12345678"
        r = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(r.status_code, 400)

    def test_register_duplicate_email(self):
        self.client.post("/api/auth/register/", self.payload, format="json")
        self.payload["username"] = "alice2"
        r = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(r.status_code, 400)

    def test_login_returns_tokens(self):
        User.objects.create_user("alice", "alice@example.com", PASSWORD)
        r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

    def test_login_wrong_password(self):
        User.objects.create_user("alice", "alice@example.com", PASSWORD)
        self.assertEqual(self.login(password="wrong-password").status_code, 401)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_me_returns_current_user(self):
        User.objects.create_user("alice", "alice@example.com", PASSWORD)
        access = self.login().data["access"]
        r = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["username"], "alice")
        self.assertNotIn("password", r.data)

    def test_logout_blacklists_refresh_token(self):
        User.objects.create_user("alice", "alice@example.com", PASSWORD)
        tokens = self.login().data
        auth = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        r = self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]},
                             format="json", **auth)
        self.assertEqual(r.status_code, 205)
        r = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]},
                             format="json")
        self.assertEqual(r.status_code, 401)

    def test_logout_rejects_someone_elses_token(self):
        User.objects.create_user("alice", "alice@example.com", PASSWORD)
        User.objects.create_user("bob", "bob@example.com", PASSWORD)
        alice = self.login("alice").data
        bob = self.login("bob").data
        r = self.client.post("/api/auth/logout/", {"refresh": alice["refresh"]},
                             format="json",
                             HTTP_AUTHORIZATION=f"Bearer {bob['access']}")
        self.assertEqual(r.status_code, 400)

    def test_logout_without_refresh_token(self):
        User.objects.create_user("alice", "alice@example.com", PASSWORD)
        access = self.login().data["access"]
        r = self.client.post("/api/auth/logout/", {}, format="json",
                             HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(r.status_code, 400)