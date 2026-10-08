from django.db import transaction as db_transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.models import AdminLog, Transaction

from .audit import log_action
from .models import Card
from .notifications import notify_card_blocked


class AdminCardSerializer(serializers.ModelSerializer):
    """Card details for staff. Only the masked number is ever exposed."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Card
        fields = (
            "id", "username", "card_holder", "brand", "masked_number", "last4",
            "expiry_month", "expiry_year", "credit_limit",
            "is_blocked", "blocked_at", "created_at",
        )
        read_only_fields = fields


class LimitSerializer(serializers.Serializer):
    credit_limit = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=1
    )


class AdminCardListView(APIView):
    """GET /api/admin/cards/ - every card in the system (staff only)."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        cards = Card.objects.select_related("user").order_by("-created_at")
        return Response(AdminCardSerializer(cards, many=True).data)


class AdminCardBlockView(APIView):
    """POST /api/admin/cards/<id>/block/"""

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        with db_transaction.atomic():
            card = get_object_or_404(
                Card.objects.select_related("user").select_for_update(of=("self",)),
                pk=pk,
            )
            if card.is_blocked:
                return Response({"detail": "Card is already blocked."}, status=400)
            card.block()
            log_action(request, "BLOCK_CARD", card, "Blocked by admin")
        # Sent after the transaction commits, so a slow mail server never holds the lock
        notify_card_blocked(card)
        return Response(AdminCardSerializer(card).data)


class AdminCardUnblockView(APIView):
    """POST /api/admin/cards/<id>/unblock/"""

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        with db_transaction.atomic():
            card = get_object_or_404(Card.objects.select_for_update(), pk=pk)
            if not card.is_blocked:
                return Response({"detail": "Card is not blocked."}, status=400)
            card.unblock()
            log_action(request, "UNBLOCK_CARD", card, "Unblocked by admin")
        return Response(AdminCardSerializer(card).data)


class AdminCardLimitView(APIView):
    """PATCH /api/admin/cards/<id>/limit/  body: {"credit_limit": "50000.00"}"""

    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        serializer = LimitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_limit = serializer.validated_data["credit_limit"]

        with db_transaction.atomic():
            card = get_object_or_404(Card.objects.select_for_update(), pk=pk)
            old_limit = card.credit_limit
            card.credit_limit = new_limit
            card.save(update_fields=["credit_limit"])
            log_action(
                request, "UPDATE_LIMIT", card,
                f"Limit changed from {old_limit} to {new_limit}",
            )
        return Response(AdminCardSerializer(card).data)


class AdminCardActivityView(APIView):
    """GET /api/admin/cards/<id>/activity/ - recent payments and admin actions."""

    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        card = get_object_or_404(Card, pk=pk)
        transactions = (
            Transaction.objects.filter(card_id=card.id)
            .order_by("-created_at")
            .values(
                "id", "reference", "amount", "currency",
                "description", "status", "failure_reason", "created_at",
            )[:10]
        )
        # "card #12 (" matches card 12 only, never card 123
        logs = (
            AdminLog.objects.filter(action__contains=f"card #{card.id} (")
            .order_by("-created_at")
            .annotate(details=F("action"))
            .values("id", "details", "created_at", "admin__username")[:10]
        )
        return Response({"transactions": list(transactions), "logs": list(logs)})