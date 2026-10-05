from rest_framework import serializers

from cards.serializers import CardSerializer
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    card_last4 = serializers.CharField(source="card.last4", read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = (
            "id", "reference", "amount", "currency", "description",
            "status", "failure_reason", "card", "card_last4", "created_at",
        )


class AdminTransactionSerializer(TransactionSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + ("username",)


class AdminCardSerializer(CardSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta(CardSerializer.Meta):
        fields = CardSerializer.Meta.fields + ("username",)