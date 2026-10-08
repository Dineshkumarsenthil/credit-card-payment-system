from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Card(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards"
    )
    card_holder = models.CharField(max_length=100)
    brand = models.CharField(max_length=20)
    masked_number = models.CharField(max_length=19)  # **** **** **** 1234
    last4 = models.CharField(max_length=4)
    expiry_month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    expiry_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    # Used by the dashboard to work out the available credit
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("100000.00")
    )
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cards"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.brand} {self.masked_number}"

    def block(self):
        self.is_blocked = True
        self.blocked_at = timezone.now()
        self.save(update_fields=["is_blocked", "blocked_at"])

    def unblock(self):
        self.is_blocked = False
        self.blocked_at = None
        self.save(update_fields=["is_blocked", "blocked_at"])