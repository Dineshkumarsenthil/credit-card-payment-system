from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from cards.models import Card
from .models import AdminLog, Transaction

User = get_user_model()


class TransactionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user("alice", "alice@example.com", "Str0ng!Pass#42")
        self.bob = User.objects.create_user("bob", "bob@example.com", "Str0ng!Pass#42")
        self.admin = User.objects.create_user(
            "boss", "boss@example.com", "Str0ng!Pass#42", is_staff=True
        )
        self.card = Card.objects.create(
            user=self.alice, card_holder="Alice", brand="VISA",
            masked_number="**** **** **** 1111", last4="1111",
            expiry_month=12, expiry_year=2035,
        )

    def make(self, user, amount, status="SUCCESS", description=""):
        return Transaction.objects.create(
            user=user, card=self.card if user == self.alice else None,
            amount=Decimal(amount), status=status, description=description,
        )

    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/api/transactions/").status_code, 401)

    def test_user_sees_only_own_transactions(self):
        self.make(self.alice, "100.00")
        self.make(self.bob, "999.00")
        self.client.force_authenticate(self.alice)
        r = self.client.get("/api/transactions/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(Decimal(r.data[0]["amount"]), Decimal("100.00"))
        self.assertEqual(r.data[0]["card_last4"], "1111")

    def test_filters(self):
        self.make(self.alice, "50.00", "FAILED")
        self.make(self.alice, "150.00", "SUCCESS")
        self.make(self.alice, "250.00", "SUCCESS")
        self.client.force_authenticate(self.alice)
        self.assertEqual(len(self.client.get("/api/transactions/?status=failed").data), 1)
        self.assertEqual(len(self.client.get("/api/transactions/?min_amount=100").data), 2)
        self.assertEqual(len(self.client.get("/api/transactions/?max_amount=100").data), 1)
        self.assertEqual(
            len(self.client.get("/api/transactions/?min_amount=100&max_amount=200").data), 1
        )

    def test_invalid_filter_values_return_400(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.get("/api/transactions/?date_from=not-a-date").status_code, 400)
        self.assertEqual(self.client.get("/api/transactions/?min_amount=abc").status_code, 400)

    def test_admin_endpoints_forbidden_for_normal_user(self):
        self.client.force_authenticate(self.alice)
        for path in ("users/", "cards/", "transactions/", "transactions/export/", "summary/"):
            r = self.client.get(f"/api/admin/{path}")
            self.assertEqual(r.status_code, 403, path)

    def test_admin_endpoints_require_authentication(self):
        self.assertEqual(self.client.get("/api/admin/users/").status_code, 401)

    def test_admin_sees_all_data(self):
        self.make(self.alice, "100.00")
        self.make(self.bob, "200.00")
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get("/api/admin/transactions/").data), 2)
        self.assertEqual(len(self.client.get("/api/admin/users/").data), 3)
        self.assertEqual(len(self.client.get("/api/admin/cards/").data), 1)

    def test_csv_export_is_safe_and_logged(self):
        self.make(self.alice, "100.00", description="=HYPERLINK(\"http://evil\")")
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/admin/transactions/export/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "text/csv")
        body = r.content.decode()
        self.assertIn("'=HYPERLINK", body)
        self.assertNotIn(",=HYPERLINK", body)
        self.assertTrue(AdminLog.objects.filter(admin=self.admin).exists())

    def test_daily_summary(self):
        self.make(self.alice, "100.00", "SUCCESS")
        self.make(self.alice, "200.00", "SUCCESS")
        self.make(self.alice, "50.00", "FAILED")
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/admin/summary/")
        self.assertEqual(r.status_code, 200)
        row = r.data[0]
        self.assertEqual(row["total"], 3)
        self.assertEqual(row["success"], 2)
        self.assertEqual(row["failed"], 1)
        self.assertEqual(row["success_amount"], Decimal("300.00"))