import os
import smtplib
from email.message import EmailMessage


def _flag(name: str) -> bool:
    return os.getenv(name, "False").strip().lower() in ("1", "true", "yes")


def send_fraud_alert(recipients: list[str], txn, reasons: list[tuple[str, str]]) -> bool:
    """Sends through the same SMTP settings as the rest of the project (Mailpit).
    Returns True if sent. Never raises, so a mail problem cannot break a payment."""
    recipients = [r for r in recipients if r]
    if not recipients:
        return False

    msg = EmailMessage()
    msg["Subject"] = f"FRAUD ALERT: payment {txn.reference[:8]} flagged"
    msg["From"] = os.getenv("EMAIL_FROM", "SecurePay <no-reply@securepay.local>")
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        "A suspicious payment was flagged for review.\n\n"
        f"Reference : {txn.reference}\n"
        f"User ID   : {txn.user_id}\n"
        f"Card ID   : {txn.card_id}\n"
        f"Amount    : {txn.amount} {txn.currency}\n"
        f"Location  : {txn.location or '-'}\n"
        f"Device    : {txn.device_id or '-'}\n\n"
        "Rules triggered:\n"
        + "\n".join(f"  - {name}: {details}" for name, details in reasons)
    )

    try:
        with smtplib.SMTP(
            os.getenv("EMAIL_HOST", "localhost"),
            int(os.getenv("EMAIL_PORT", "1025")),
            timeout=5,
        ) as server:
            if _flag("EMAIL_USE_TLS"):
                server.starttls()
            user = os.getenv("EMAIL_HOST_USER", "")
            if user:
                server.login(user, os.getenv("EMAIL_HOST_PASSWORD", ""))
            server.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[fraud] email failed: {exc}")
        return False