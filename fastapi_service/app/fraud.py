import os
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .emailer import send_fraud_alert
from .models import FraudLog, Transaction, User

HIGH_VALUE_AMOUNT = float(os.getenv("FRAUD_HIGH_VALUE", "5000"))
HIGH_VALUE_COUNT = int(os.getenv("FRAUD_HIGH_VALUE_COUNT", "3"))
HIGH_VALUE_WINDOW_MIN = int(os.getenv("FRAUD_HIGH_VALUE_WINDOW_MIN", "10"))
LOCATION_WINDOW_MIN = int(os.getenv("FRAUD_LOCATION_WINDOW_MIN", "5"))
ALERT_TO = os.getenv("FRAUD_ALERT_TO", "security@securepay.local")


def _same(a: str | None, b: str | None) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def _rule_high_value(db: Session, txn: Transaction):
    """Rule 1: several high-value payments by one user in a short time."""
    if float(txn.amount) < HIGH_VALUE_AMOUNT:
        return None
    since = txn.created_at - timedelta(minutes=HIGH_VALUE_WINDOW_MIN)
    count = db.scalar(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == txn.user_id,
            Transaction.amount >= HIGH_VALUE_AMOUNT,
            Transaction.created_at >= since,
            Transaction.created_at <= txn.created_at,
        )
    ) or 0
    if count >= HIGH_VALUE_COUNT:
        return (
            "MULTIPLE_HIGH_VALUE",
            f"{count} payments of {HIGH_VALUE_AMOUNT:.0f} or more within "
            f"{HIGH_VALUE_WINDOW_MIN} minutes",
        )
    return None


def _rule_location_device(db: Session, txn: Transaction):
    """Rule 2: rapid payments from different locations or devices. Returns a list."""
    since = txn.created_at - timedelta(minutes=LOCATION_WINDOW_MIN)
    others = db.scalars(
        select(Transaction)
        .where(
            Transaction.user_id == txn.user_id,
            Transaction.id != txn.id,
            Transaction.created_at >= since,
        )
        .order_by(Transaction.created_at.desc())
        .limit(20)
    ).all()

    hits = []
    for o in others:
        if txn.location and o.location and not _same(txn.location, o.location):
            hits.append((
                "RAPID_DIFFERENT_LOCATION",
                f"'{o.location}' then '{txn.location}' within {LOCATION_WINDOW_MIN} minutes",
            ))
            break
    for o in others:
        if txn.device_id and o.device_id and not _same(txn.device_id, o.device_id):
            hits.append((
                "RAPID_DIFFERENT_DEVICE",
                f"device changed within {LOCATION_WINDOW_MIN} minutes",
            ))
            break
    return hits


def evaluate_transaction(db: Session, txn: Transaction) -> list[tuple[str, str]]:
    """Call after the payment is saved. Flags it, logs it and sends the email alert."""
    reasons = []
    r1 = _rule_high_value(db, txn)
    if r1:
        reasons.append(r1)
    reasons.extend(_rule_location_device(db, txn))

    if not reasons:
        return []

    txn.fraud_status = "flagged"

    recipients = [ALERT_TO]
    owner = db.get(User, txn.user_id)
    if owner and owner.email:
        recipients.append(owner.email)
    email_sent = send_fraud_alert(recipients, txn, reasons)

    for rule, details in reasons:
        db.add(
            FraudLog(
                transaction_id=txn.id,
                user_id=txn.user_id,
                card_id=txn.card_id,
                rule_triggered=rule,
                details=details[:255],
                email_sent=email_sent,
            )
        )
    db.commit()
    return reasons