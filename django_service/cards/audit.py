from transactions.models import AdminLog


def log_action(request, action, card, details=""):
    """Write one admin action to the admin_logs table.

    AdminLog only has admin, action and created_at, so the card id and masked
    number go inside the action text. The activity view finds them by "card #<id> (".
    """
    text = f"{action} - card #{card.pk} ({card.masked_number}) - {details}"
    return AdminLog.objects.create(admin=request.user, action=text[:255])