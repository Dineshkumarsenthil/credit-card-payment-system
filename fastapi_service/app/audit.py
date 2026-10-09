from sqlalchemy.orm import Session

from .models import AuditLog


def log_admin_action(
    db: Session,
    user_id: int,
    action: str,
    card_id: int | None = None,
    old_value=None,
    new_value=None,
) -> None:
    """Adds an audit row. The caller commits, so the change and its log save together."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            card_id=card_id,
            old_value=None if old_value is None else str(old_value),
            new_value=None if new_value is None else str(new_value),
        )
    )