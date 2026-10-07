"""GET /dashboard/summary - quick card-usage stats for the logged-in user.

Assumed names (rename to match your project if they differ):
  .auth.get_current_user_id  -> returns the user id from the JWT, raises 401 if invalid
  .database.get_db           -> yields a SQLAlchemy Session
  .models.Card / .models.Transaction
"""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from .auth import get_current_user_id
from .database import get_db
from .models import Card, Transaction

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class RecentTransaction(BaseModel):
    amount: Decimal
    masked_card: str
    date: datetime
    status: str


class DashboardSummary(BaseModel):
    total_transactions: int
    total_amount_spent: Decimal
    current_month_spending: Decimal
    available_credit_limit: Decimal
    last_5_transactions: list[RecentTransaction]


@router.get("/summary", response_model=DashboardSummary, summary="Dashboard summary")
def dashboard_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Counts every payment; money totals count SUCCESS payments only,
    because PENDING and FAILED payments never moved money."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # DB stores UTC
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    paid = Transaction.status == "SUCCESS"

    # 1) one aggregate query over transactions: COUNT + SUM(amount)
    total_count, total_spent, month_spent = db.execute(
        select(
            func.count(Transaction.id),
            func.coalesce(func.sum(case((paid, Transaction.amount), else_=0)), 0),
            func.coalesce(
                func.sum(
                    case((and_(paid, Transaction.created_at >= month_start),
                          Transaction.amount), else_=0)
                ),
                0,
            ),
        ).where(Transaction.user_id == user_id)
    ).one()

    # 2) credit limit from the cards table: SUM(credit_limit)
    total_limit = db.execute(
        select(func.coalesce(func.sum(Card.credit_limit), 0)).where(Card.user_id == user_id)
    ).scalar_one()

    # 3) last 5 transactions joined to cards for the masked number: ORDER BY + LIMIT 5
    rows = db.execute(
        select(
            Transaction.amount,
            Card.masked_number,
            Transaction.created_at,
            Transaction.status,
        )
        .join(Card, Card.id == Transaction.card_id, isouter=True)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(5)
    ).all()

    return DashboardSummary(
        total_transactions=total_count,
        total_amount_spent=total_spent,
        current_month_spending=month_spent,
        available_credit_limit=max(Decimal(total_limit) - Decimal(total_spent), Decimal("0")),
        last_5_transactions=[
            RecentTransaction(
                amount=r.amount,
                masked_card=r.masked_number or "Card removed",
                date=r.created_at,
                status=r.status,
            )
            for r in rows
        ],
    )