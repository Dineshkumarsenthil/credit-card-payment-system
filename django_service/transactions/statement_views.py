import re
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.models import Card

from .models import Transaction
from .statement_pdf import build_statement_pdf

MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def month_bounds(year: int, month: int):
    """First moment of the month and first moment of the next month."""
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    if settings.USE_TZ:
        tz = timezone.get_current_timezone()
        start, end = timezone.make_aware(start, tz), timezone.make_aware(end, tz)
    return start, end


def to_local(value):
    return timezone.localtime(value) if timezone.is_aware(value) else value


class MonthlyStatementView(APIView):
    """GET /api/statements/?month=2026-10

    Returns a PDF for the logged-in user only. The user comes from the JWT,
    never from the URL, so nobody can request another person's statement.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        match = MONTH_RE.match(request.query_params.get("month", ""))
        if not match:
            return Response({"detail": "month is required in YYYY-MM format."}, status=400)
        year, month = int(match[1]), int(match[2])
        if not 1 <= month <= 12 or year < 2000:
            return Response({"detail": "Invalid month."}, status=400)
        today = date.today()
        if (year, month) > (today.year, today.month):
            return Response({"detail": "A statement cannot be created for a future month."},
                            status=400)

        user = request.user
        start, end = month_bounds(year, month)

        cards = list(Card.objects.filter(user=user).order_by("id"))
        card_by_id = {c.id: c for c in cards}

        txns = Transaction.objects.filter(
            user_id=user.id, created_at__gte=start, created_at__lt=end
        ).order_by("created_at")

        counts = {"total": 0, "success": 0, "failed": 0, "pending": 0}
        total_spent = Decimal("0")
        rows = []
        for t in txns:
            counts["total"] += 1
            counts[t.status.lower()] = counts.get(t.status.lower(), 0) + 1
            if t.status == "SUCCESS":
                total_spent += t.amount
            card = card_by_id.get(t.card_id)
            rows.append({
                "date": to_local(t.created_at),
                "card": f"**** {card.last4}" if card else "-",
                "description": (t.description or "")[:80],
                "status": t.status,
                "amount": t.amount,
            })

        # Available credit uses the same rule as FastAPI: limit minus all
        # successful spending on the card
        spent_by_card = dict(
            Transaction.objects.filter(
                user_id=user.id, status="SUCCESS", card_id__in=list(card_by_id)
            )
            .order_by()
            .values("card_id")
            .annotate(total=Sum("amount"))
            .values_list("card_id", "total")
        )
        card_rows = []
        available_total = Decimal("0")
        for c in cards:
            available = c.credit_limit - spent_by_card.get(c.id, Decimal("0"))
            available_total += available
            card_rows.append({
                "masked": f"**** {c.last4}",
                "brand": c.brand,
                "limit": c.credit_limit,
                "available": available,
                "blocked": c.is_blocked,
            })

        last_day = (end - start).days
        data = {
            "holder": user.get_full_name() or user.username,
            "period_start": date(year, month, 1),
            "period_end": date(year, month, last_day),
            "generated_at": to_local(timezone.now()) if settings.USE_TZ else datetime.now(),
            "cards": card_rows,
            "rows": rows,
            "total_spent": total_spent,
            "counts": counts,
            "available_credit": available_total,
        }

        buffer = BytesIO()
        build_statement_pdf(buffer, data)
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="statement-{year}-{month:02d}.pdf"'
        response["Cache-Control"] = "no-store"
        return response