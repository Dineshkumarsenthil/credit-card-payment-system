from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "brand", "masked_number", "expiry_month", "expiry_year", "created_at")
    search_fields = ("user__username", "last4")
    list_filter = ("brand",)