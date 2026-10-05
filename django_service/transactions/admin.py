from django.contrib import admin

from .models import AdminLog, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "currency", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "user__username")


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ("admin", "action", "created_at")