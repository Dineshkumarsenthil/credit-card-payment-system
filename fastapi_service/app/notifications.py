import logging
import os
import smtplib
from decimal import Decimal
from email.message import EmailMessage

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Card, Transaction, User

logger = logging.getLogger("notifications")

# All settings come from .env. The SMTP password is never hard-coded or logged.
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM", "SecurePay <no-reply@securepay.local>")
ALERT_AMOUNT = Decimal(os.getenv("ALERT_AMOUNT", "5000"))
LOW_CREDIT_PERCENT = Decimal(os.getenv("LOW_CREDIT_PERCENT", "10"))


def _mask(masked_number: str) -> str:
    return f"**** {masked_number[-4:]}"


def _money(amount, currency="INR") -> str:
    symbol = "₹" if currency == "INR" else f"{currency} "
    return f"{symbol}{Decimal(amount):,.2f}"


def _send(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10) as smtp:
            if EMAIL_USE_TLS:
                smtp.starttls()
            if EMAIL_HOST_USER:
                smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            smtp.send_message(msg)
    except Exception:
        # The payment already succeeded, so a mail problem is only logged
        logger.exception("Could not send '%s' email", subject)


def send_large_payment_alert(to, masked, amount, currency, reference):
    _send(
        to,
        f"Payment of {_money(amount, currency)} on card {masked}",
        f"A payment of {_money(amount, currency)} was made with your card {masked}.\n"
        f"Reference: {reference}\n\n"
        f"We alert you about every payment above {_money(ALERT_AMOUNT)}.\n"
        f"If you did not make this payment, contact SecurePay support.\n\n"
        f"SecurePay",
    )


def send_low_credit_alert(to, masked, available, limit):
    _send(
        to,
        f"Low available credit on card {masked}",
        f"The available credit on your card {masked} is now {_money(available)}, "
        f"below {LOW_CREDIT_PERCENT:g}% of your {_money(limit)} limit.\n\n"
        f"SecurePay",
    )


def queue_payment_alerts(
    background: BackgroundTasks,
    db: Session,
    card: Card,
    txn: Transaction,
    available_after: Decimal,
) -> None:
    """Queue the alerts for a payment. Call it after the payment has succeeded."""
    if txn.status != "SUCCESS":
        return

    is_large = txn.amount > ALERT_AMOUNT

    # Alert when this payment pushes the available credit under the threshold
    threshold = Decimal(card.credit_limit) * LOW_CREDIT_PERCENT / 100
    available_before = available_after + txn.amount
    is_low = available_after < threshold <= available_before

    if not (is_large or is_low):
        return

    email = db.scalar(select(User.email).where(User.id == card.user_id))
    if not email:
        logger.warning("No email on file for user %s, alert skipped", card.user_id)
        return

    masked = _mask(card.masked_number)
    if is_large:
        background.add_task(
            send_large_payment_alert, email, masked, txn.amount, txn.currency, txn.reference
        )
    if is_low:
        background.add_task(
            send_low_credit_alert, email, masked, available_after, card.credit_limit
        )