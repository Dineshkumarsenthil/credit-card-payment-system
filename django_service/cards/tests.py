from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import Card

User = get_user_model()


class CardTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user("alice", "alice@example.com", "Str0ng!Pass#42")
        self.bob = User.objects.create_user("bob", "bob@example.com", "Str0ng!Pass#42")
        self.valid = {
            "card_holder": "Alice", "card_number": "4111 1111 1111 1111", "cvv": "123",
            "expiry_month": 12, "expiry_year": date.today().year + 3,
        }

    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/api/cards/").status_code, 401)
        self.assertEqual(self.client.post("/api/cards/", self.valid, format="json").status_code, 401)

    def test_create_card_never_stores_cvv_or_full_number(self):
        self.client.force_authenticate(self.alice)
        r = self.client.post("/api/cards/", self.valid, format="json")
        self.assertEqual(r.status_code, 201)
        for secret_key in ("cvv", "card_number"):
            self.assertNotIn(secret_key, r.data)
        self.assertEqual(r.data["last4"], "1111")
        self.assertEqual(r.data["brand"], "VISA")
        self.assertEqual(r.data["masked_number"], "**** **** **** 1111")

        card = Card.objects.get(pk=r.data["id"])
        field_names = [f.name for f in Card._meta.get_fields()]
        self.assertNotIn("cvv", field_names)
        stored = " ".join(str(getattr(card, f.name)) for f in Card._meta.concrete_fields)
        self.assertNotIn("4111111111111111", stored)
        self.assertNotIn("123", card.masked_number)

    def test_invalid_luhn_rejected(self):
        self.client.force_authenticate(self.alice)
        self.valid["card_number"] = "4111 1111 1111 1112"
        self.assertEqual(self.client.post("/api/cards/", self.valid, format="json").status_code, 400)

    def test_expired_card_rejected(self):
        self.client.force_authenticate(self.alice)
        self.valid.update(expiry_month=1, expiry_year=2020)
        self.assertEqual(self.client.post("/api/cards/", self.valid, format="json").status_code, 400)

    def test_bad_cvv_rejected(self):
        self.client.force_authenticate(self.alice)
        for bad in ("12", "12345", "abc"):
            self.valid["cvv"] = bad
            r = self.client.post("/api/cards/", self.valid, format="json")
            self.assertEqual(r.status_code, 400, bad)

    def test_user_only_sees_own_cards(self):
        self.client.force_authenticate(self.alice)
        self.client.post("/api/cards/", self.valid, format="json")
        self.client.force_authenticate(self.bob)
        r = self.client.get("/api/cards/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 0)

    def test_cannot_delete_someone_elses_card(self):
        self.client.force_authenticate(self.alice)
        card_id = self.client.post("/api/cards/", self.valid, format="json").data["id"]
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.delete(f"/api/cards/{card_id}/").status_code, 404)
        self.assertTrue(Card.objects.filter(pk=card_id).exists())

    def test_owner_can_delete_card(self):
        self.client.force_authenticate(self.alice)
        card_id = self.client.post("/api/cards/", self.valid, format="json").data["id"]
        self.assertEqual(self.client.delete(f"/api/cards/{card_id}/").status_code, 204)
        self.assertFalse(Card.objects.filter(pk=card_id).exists())