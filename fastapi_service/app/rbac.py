from dataclasses import dataclass

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import get_current_user_id
from .database import get_db
from .models import UserRole

ROLE_DESCRIPTIONS = {
    "admin": "Full access: cards, limits, analytics, audit/fraud logs, health, role management",
    "support": "View cards/transactions/analytics and block or unblock cards (no limit changes)",
    "readonly": "View cards, transactions and analytics only",
}

PERMISSIONS = {
    "admin": {
        "card:view", "card:block", "card:limit",
        "txn:view", "analytics:view",
        "audit:view", "health:view", "role:manage",
    },
    "support": {"card:view", "card:block", "txn:view", "analytics:view"},
    "readonly": {"card:view", "txn:view", "analytics:view"},
}


@dataclass
class Staff:
    user_id: int
    role: str


def get_role(db: Session, user_id: int) -> str | None:
    row = db.get(UserRole, user_id)
    return row.role if row else None


def require_permission(permission: str):
    """Usage: staff = Depends(require_permission("card:block"))"""

    def checker(
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
    ) -> Staff:
        role = get_role(db, user_id)
        if role is None:
            raise HTTPException(status_code=403, detail="No staff role assigned to this user")
        if permission not in PERMISSIONS.get(role, set()):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' is not allowed to perform '{permission}'",
            )
        return Staff(user_id=user_id, role=role)

    return checker