from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .exports import build_csv, build_pdf
from .models import Card, Transaction
from .rbac import Staff, require_permission

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _spend(user_id: int | None):
    conds = [Transaction.status == "SUCCESS"]
    if user_id is not None:
        conds.append(Transaction.user_id == user_id)
    return conds


def monthly(db: Session, user_id: int | None = None):
    month = func.date_format(Transaction.created_at, "%Y-%m").label("month")
    rows = db.execute(
        select(month, func.coalesce(func.sum(Transaction.amount), 0), func.count(Transaction.id))
        .where(*_spend(user_id))
        .group_by(month)
        .order_by(month)
    ).all()
    return [{"month": m, "total": float(t), "count": c} for m, t, c in rows]


def categories(db: Session, user_id: int | None = None):
    cat = func.coalesce(Transaction.category, "Other").label("category")
    total = func.sum(Transaction.amount)
    rows = db.execute(
        select(cat, total, func.count(Transaction.id))
        .where(*_spend(user_id))
        .group_by(cat)
        .order_by(total.desc())
    ).all()
    return [{"category": c, "total": float(t or 0), "count": n} for c, t, n in rows]


def spent_by_card(db: Session, card_ids=None, user_id: int | None = None) -> dict:
    stmt = select(Transaction.card_id, func.sum(Transaction.amount)).where(
        Transaction.card_id.isnot(None), *_spend(user_id)
    )
    if card_ids is not None:
        stmt = stmt.where(Transaction.card_id.in_(card_ids))
    stmt = stmt.group_by(Transaction.card_id)
    return {cid: Decimal(total) for cid, total in db.execute(stmt).all()}


def utilization(db: Session, user_id: int | None = None):
    card_stmt = select(Card).order_by(Card.id)
    if user_id is not None:
        card_stmt = card_stmt.where(Card.user_id == user_id)
    cards = db.scalars(card_stmt).all()
    spent = spent_by_card(db, user_id=user_id)

    items, total_limit, total_spent = [], Decimal(0), Decimal(0)
    for c in cards:
        limit = Decimal(c.credit_limit or 0)
        used = spent.get(c.id, Decimal(0))
        total_limit += limit
        total_spent += used
        items.append({
            "card_id": c.id,
            "card": c.masked_number,
            "limit": float(limit),
            "spent": float(used),
            "percent": round(float(used / limit * 100), 2) if limit else 0,
        })
    overall = round(float(total_spent / total_limit * 100), 2) if total_limit else 0
    return {"overall_percent": overall, "cards": items}


def summary(db: Session, user_id: int | None = None):
    return {
        "monthly": monthly(db, user_id),
        "categories": categories(db, user_id),
        "utilization": utilization(db, user_id),
    }


@router.get("/monthly", summary="Monthly spending summary")
def monthly_api(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("analytics:view")),
):
    return monthly(db, user_id)


@router.get("/categories", summary="Category-wise expense data")
def categories_api(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("analytics:view")),
):
    return categories(db, user_id)


@router.get("/utilization", summary="Credit utilization percentage")
def utilization_api(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("analytics:view")),
):
    return utilization(db, user_id)


@router.get("/summary", summary="All analytics in one response")
def summary_api(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("analytics:view")),
):
    return summary(db, user_id)


@router.get("/export", summary="Export analytics summary as CSV or PDF")
def export_api(
    format: Literal["csv", "pdf"] = Query("csv"),
    user_id: int | None = None,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("analytics:view")),
):
    data = summary(db, user_id)
    if format == "csv":
        return Response(
            content=build_csv(data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_summary.csv"},
        )
    return Response(
        content=build_pdf(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=analytics_summary.pdf"},
    )