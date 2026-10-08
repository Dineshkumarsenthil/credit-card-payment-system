from django.contrib import admin

from .audit import log_action
from .models import Card
from .notifications import notify_card_blocked


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "brand", "masked_number", "credit_limit",
        "is_blocked", "expiry_month", "expiry_year", "created_at",
    )
    search_fields = ("user__username", "last4")
    list_filter = ("brand", "is_blocked")
    readonly_fields = ("blocked_at",)
    actions = ["block_selected", "unblock_selected"]

    @admin.action(description="Block selected cards")
    def block_selected(self, request, queryset):
        count = 0
        for card in queryset.select_related("user").filter(is_blocked=False):
            card.block()
            log_action(request, "BLOCK_CARD", card, f"Blocked card {card.masked_number} (Django admin)")
            notify_card_blocked(card)
            count += 1
        self.message_user(request, f"{count} card(s) blocked.")

    @admin.action(description="Unblock selected cards")
    def unblock_selected(self, request, queryset):
        count = 0
        for card in queryset.filter(is_blocked=True):
            card.unblock()
            log_action(request, "UNBLOCK_CARD", card, f"Unblocked card {card.masked_number} (Django admin)")
            count += 1
        self.message_user(request, f"{count} card(s) unblocked.")