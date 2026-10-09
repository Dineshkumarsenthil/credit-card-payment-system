import time
from datetime import timedelta
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .analytics import spent_by_card
from .audit import log_admin_action
from .auth import get_current_user_id
from .database import get_db
from .models import ApiLog, AuditLog, Card, FraudLog, User, UserRole, utcnow
from .rbac import PERMISSIONS, Staff, get_role, require_permission

router = APIRouter(prefix="/admin", tags=["Admin"])
STARTED = time.time()


class LimitIn(BaseModel):
    credit_limit: Decimal = Field(gt=0, le=10_000_000, max_digits=12, decimal_places=2)


class RoleIn(BaseModel):
    user_id: int
    role: Literal["admin", "support", "readonly"]


@router.get("/me", summary="My staff role and permissions")
def my_role(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    role = get_role(db, user_id)
    return {
        "user_id": user_id,
        "role": role,
        "permissions": sorted(PERMISSIONS.get(role, set())) if role else [],
    }


# ---------------- Card management ----------------
@router.get("/cards", summary="List all cards (masked)")
def list_cards(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("card:view")),
):
    cards = db.scalars(select(Card).order_by(Card.id).limit(limit).offset(offset)).all()
    spent = spent_by_card(db, card_ids=[c.id for c in cards]) if cards else {}
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "masked_number": c.masked_number,
            "credit_limit": float(c.credit_limit),
            "spent": float(spent.get(c.id, 0)),
            "is_blocked": bool(c.is_blocked),
        }
        for c in cards
    ]


def _set_blocked(db: Session, staff: Staff, card_id: int, blocked: bool):
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    if bool(card.is_blocked) == blocked:
        raise HTTPException(
            status_code=400,
            detail="Card is already blocked" if blocked else "Card is not blocked",
        )
    card.is_blocked = blocked
    log_admin_action(
        db, staff.user_id,
        "CARD_BLOCK" if blocked else "CARD_UNBLOCK",
        card.id,
        "ACTIVE" if blocked else "BLOCKED",
        "BLOCKED" if blocked else "ACTIVE",
    )
    db.commit()
    return {"card_id": card.id, "is_blocked": blocked, "done_by_role": staff.role}


@router.post("/cards/{card_id}/block", summary="Block a card")
def block_card(
    card_id: int,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("card:block")),
):
    return _set_blocked(db, staff, card_id, True)


@router.post("/cards/{card_id}/unblock", summary="Unblock a card")
def unblock_card(
    card_id: int,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("card:block")),
):
    return _set_blocked(db, staff, card_id, False)


@router.post("/cards/{card_id}/limit", summary="Update a card's credit limit (admin only)")
def update_limit(
    card_id: int,
    payload: LimitIn,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("card:limit")),
):
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    old = card.credit_limit
    card.credit_limit = payload.credit_limit
    log_admin_action(db, staff.user_id, "LIMIT_UPDATE", card.id, old, payload.credit_limit)
    db.commit()
    return {"card_id": card.id, "old_limit": float(old), "new_limit": float(payload.credit_limit)}


# ---------------- Roles ----------------
@router.post("/roles", summary="Assign a staff role to a user (admin only)")
def assign_role(
    payload: RoleIn,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("role:manage")),
):
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    row = db.get(UserRole, payload.user_id)
    old = row.role if row else None
    if row is None:
        db.add(UserRole(user_id=payload.user_id, role=payload.role))
    else:
        row.role = payload.role
    log_admin_action(db, staff.user_id, "ROLE_ASSIGN", None, old, f"user {payload.user_id}: {payload.role}")
    db.commit()
    return {"user_id": payload.user_id, "role": payload.role}


# ---------------- Logs ----------------
@router.get("/audit-logs", summary="Admin action audit log")
def audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("audit:view")),
):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [
        {
            "id": r.id, "user_id": r.user_id, "action": r.action, "card_id": r.card_id,
            "old_value": r.old_value, "new_value": r.new_value,
            "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]


@router.get("/fraud-logs", summary="Detected fraud attempts")
def fraud_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("audit:view")),
):
    rows = db.scalars(select(FraudLog).order_by(FraudLog.id.desc()).limit(limit)).all()
    return [
        {
            "id": r.id, "transaction_id": r.transaction_id, "user_id": r.user_id,
            "card_id": r.card_id, "rule_triggered": r.rule_triggered, "details": r.details,
            "email_sent": bool(r.email_sent), "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]


# ---------------- Health ----------------
@router.get("/health", summary="System health (admin only)")
def system_health(
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_permission("health:view")),
):
    since = utcnow() - timedelta(hours=24)
    in_window = ApiLog.created_at >= since

    total = db.scalar(select(func.count(ApiLog.id)).where(in_window)) or 0
    avg_ms = db.scalar(select(func.avg(ApiLog.response_time_ms)).where(in_window)) or 0
    server_errors = db.scalar(
        select(func.count(ApiLog.id)).where(in_window, ApiLog.status_code >= 500)) or 0
    client_errors = db.scalar(
        select(func.count(ApiLog.id)).where(in_window, ApiLog.status_code >= 400, ApiLog.status_code < 500)) or 0

    slowest = db.execute(
        select(ApiLog.endpoint, func.avg(ApiLog.response_time_ms), func.count(ApiLog.id))
        .where(in_window)
        .group_by(ApiLog.endpoint)
        .order_by(func.avg(ApiLog.response_time_ms).desc())
        .limit(5)
    ).all()

    recent_errors = db.scalars(
        select(ApiLog).where(ApiLog.status_code >= 400).order_by(ApiLog.id.desc()).limit(10)
    ).all()

    try:
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:  # noqa: BLE001
        db_status = "down"

    return {
        "status": "healthy" if db_status == "up" else "degraded",
        "database": db_status,
        "uptime_seconds": int(time.time() - STARTED),
        "last_24h": {
            "total_requests": total,
            "avg_response_ms": round(float(avg_ms), 2),
            "server_errors": server_errors,
            "client_errors": client_errors,
            "error_rate_percent": round(server_errors / total * 100, 2) if total else 0,
        },
        "slowest_endpoints": [
            {"endpoint": e, "avg_ms": round(float(a), 2), "hits": h} for e, a, h in slowest
        ],
        "recent_errors": [
            {
                "endpoint": r.endpoint, "method": r.method, "status_code": r.status_code,
                "response_ms": r.response_time_ms, "error": r.error_message,
                "created_at": r.created_at.isoformat() + "Z",
            }
            for r in recent_errors
        ],
    }