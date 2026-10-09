from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import get_current_user_id
from .database import get_db
from .models import Card, Transaction
from .rbac import Staff, require_permission

router = APIRouter(tags=["Transactions"])

SORTABLE = {
    "id": Transaction.id,
    "created_at": Transaction.created_at,
    "amount": Transaction.amount,
    "status": Transaction.status,
    "category": Transaction.category,
}


class SearchParams:
    def __init__(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        min_amount: Decimal | None = Query(None, ge=0),
        max_amount: Decimal | None = Query(None, ge=0),
        status: Literal["PENDING", "SUCCESS", "FAILED"] | None = None,
        card: str | None = Query(None, pattern=r"^[0-9]{1,4}$",
                                 description="Last 1-4 digits of the masked card number"),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        sort_by: Literal["id", "created_at", "amount", "status", "category"] = "created_at",
        order: Literal["asc", "desc"] = "desc",
    ):
        self.date_from, self.date_to = date_from, date_to
        self.min_amount, self.max_amount = min_amount, max_amount
        self.status, self.card = status, card
        self.page, self.page_size = page, page_size
        self.sort_by, self.order = sort_by, order


def run_search(db: Session, p: SearchParams, user_id: int | None):
    conds = []
    if user_id is not None:
        conds.append(Transaction.user_id == user_id)
    if p.date_from:
        conds.append(Transaction.created_at >= datetime.combine(p.date_from, time.min))
    if p.date_to:
        conds.append(Transaction.created_at < datetime.combine(p.date_to + timedelta(days=1), time.min))
    if p.min_amount is not None:
        conds.append(Transaction.amount >= p.min_amount)
    if p.max_amount is not None:
        conds.append(Transaction.amount <= p.max_amount)
    if p.status:
        conds.append(Transaction.status == p.status)
    if p.card:
        conds.append(Card.masked_number.like(f"%{p.card}"))

    join_on = Card.id == Transaction.card_id
    total = db.scalar(
        select(func.count()).select_from(Transaction).outerjoin(Card, join_on).where(*conds)
    ) or 0

    col = SORTABLE[p.sort_by]
    rows = db.execute(
        select(Transaction, Card.masked_number)
        .outerjoin(Card, join_on)
        .where(*conds)
        .order_by(col.desc() if p.order == "desc" else col.asc(), Transaction.id.desc())
        .limit(p.page_size)
        .offset((p.page - 1) * p.page_size)
    ).all()

    return {
        "items": [
            {
                "id": t.id,
                "reference": t.reference,
                "user_id": t.user_id,
                "card": masked or "-",
                "amount": float(t.amount),
                "currency": t.currency,
                "category": t.category,
                "status": t.status,
                "fraud_status": t.fraud_status,
                "created_at": t.created_at.isoformat() + "Z",
            }
            for t, masked in rows
        ],
        "total": total,
        "page": p.page,
        "page_size": p.page_size,
        "pages": (total + p.page_size - 1) // p.page_size,
    }


@router.get("/transactions/search", summary="Search my transactions")
def search_my_transactions(
    p: SearchParams = Depends(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return run_search(db, p, user_id)


@router.get("/admin/transactions/search", summary="Search all transactions (staff)")
def search_all_transactions(
    p: SearchParams = Depends(),
    user_id: int | None = None,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("txn:view")),
):
    return run_search(db, p, user_id)