import csv
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import UserSerializer
from cards.models import Card
from .models import AdminLog, Transaction
from .serializers import (
    AdminCardSerializer, AdminTransactionSerializer, TransactionSerializer,
)


def apply_filters(qs, params):
    """Filter by status, amount range and date range (all optional)."""
    try:
        if params.get("status"):
            qs = qs.filter(status=params["status"].upper())
        if params.get("min_amount"):
            qs = qs.filter(amount__gte=Decimal(params["min_amount"]))
        if params.get("max_amount"):
            qs = qs.filter(amount__lte=Decimal(params["max_amount"]))
        if params.get("date_from"):
            qs = qs.filter(created_at__date__gte=date.fromisoformat(params["date_from"]))
        if params.get("date_to"):
            qs = qs.filter(created_at__date__lte=date.fromisoformat(params["date_to"]))
    except (InvalidOperation, ValueError):
        raise ValidationError("Invalid filter value. Use YYYY-MM-DD dates and numeric amounts.")
    return qs


def csv_safe(value):
    """Prevent CSV/Excel formula injection."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).select_related("card")
        return apply_filters(qs, self.request.query_params)


class AdminTransactionListView(generics.ListAPIView):
    serializer_class = AdminTransactionSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = Transaction.objects.select_related("user", "card")
        return apply_filters(qs, self.request.query_params)


class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.order_by("-date_joined")


class AdminCardListView(generics.ListAPIView):
    serializer_class = AdminCardSerializer
    permission_classes = [IsAdminUser]
    queryset = Card.objects.select_related("user")


class AdminExportCSVView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = apply_filters(
            Transaction.objects.select_related("user", "card"), request.query_params
        )
        AdminLog.objects.create(admin=request.user, action="Exported transactions to CSV")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(["Reference", "User", "Card", "Amount", "Currency",
                         "Status", "Description", "Created At"])
        for t in qs:
            writer.writerow([
                t.reference, csv_safe(t.user.username),
                f"**** {t.card.last4}" if t.card else "",
                t.amount, t.currency, t.status,
                csv_safe(t.description), t.created_at.isoformat(),
            ])
        return response


class AdminDailySummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        rows = (
            Transaction.objects.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                total=Count("id"),
                success=Count("id", filter=Q(status="SUCCESS")),
                failed=Count("id", filter=Q(status="FAILED")),
                pending=Count("id", filter=Q(status="PENDING")),
                success_amount=Sum("amount", filter=Q(status="SUCCESS")),
            )
            .order_by("-day")
        )
        return Response(list(rows))