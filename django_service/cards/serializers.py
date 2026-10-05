from datetime import date

from rest_framework import serializers

from .models import Card


def luhn_valid(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def detect_brand(number: str) -> str:
    if number.startswith("4"):
        return "VISA"
    if number[:2] in {"51", "52", "53", "54", "55"} or 2221 <= int(number[:4]) <= 2720:
        return "MASTERCARD"
    if number[:2] in {"34", "37"}:
        return "AMEX"
    return "OTHER"


class CardSerializer(serializers.ModelSerializer):
    """Read-only view of a saved card (safe fields only)."""

    class Meta:
        model = Card
        fields = (
            "id", "card_holder", "brand", "masked_number", "last4",
            "expiry_month", "expiry_year", "created_at",
        )


class CardCreateSerializer(serializers.Serializer):
    card_holder = serializers.CharField(max_length=100)
    card_number = serializers.CharField(write_only=True)
    cvv = serializers.CharField(write_only=True)
    expiry_month = serializers.IntegerField(min_value=1, max_value=12)
    expiry_year = serializers.IntegerField(min_value=2000, max_value=2100)

    def validate_card_number(self, value):
        number = value.replace(" ", "").replace("-", "")
        if not number.isdigit() or not 13 <= len(number) <= 19:
            raise serializers.ValidationError("Card number must be 13-19 digits.")
        if not luhn_valid(number):
            raise serializers.ValidationError("Invalid card number.")
        return number

    def validate_cvv(self, value):
        # Validated for format only, then discarded. Never stored.
        if not value.isdigit() or len(value) not in (3, 4):
            raise serializers.ValidationError("CVV must be 3 or 4 digits.")
        return value

    def validate(self, attrs):
        today = date.today()
        year, month = attrs["expiry_year"], attrs["expiry_month"]
        if (year, month) < (today.year, today.month):
            raise serializers.ValidationError("Card has expired.")
        return attrs

    def create(self, validated_data):
        number = validated_data.pop("card_number")
        validated_data.pop("cvv")  # discard, never persisted
        last4 = number[-4:]
        return Card.objects.create(
            user=validated_data["user"],
            card_holder=validated_data["card_holder"],
            brand=detect_brand(number),
            masked_number=f"**** **** **** {last4}",
            last4=last4,
            expiry_month=validated_data["expiry_month"],
            expiry_year=validated_data["expiry_year"],
        )