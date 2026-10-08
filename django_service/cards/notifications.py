import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_card_blocked(card):
    """Email the cardholder that their card was blocked.

    Shows only the masked card (**** 1234). A mail failure is logged and never
    stops the block itself from succeeding.
    """
    user = card.user
    if not user.email:
        logger.warning("Card %s blocked, but user %s has no email", card.pk, user.pk)
        return False

    masked = f"**** {card.last4}"
    name = user.get_full_name() or user.username
    subject = f"Your card {masked} has been blocked"
    body = (
        f"Hello {name},\n\n"
        f"Your {card.brand} card {masked} has been blocked and can no longer be "
        f"used for payments.\n\n"
        f"If you did not expect this, please contact SecurePay support.\n\n"
        f"SecurePay"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception:
        logger.exception("Could not send card-blocked email for card %s", card.pk)
        return False
    return True