from django.urls import path

from . import views

urlpatterns = [
    path("transactions/", views.TransactionListView.as_view()),
    path("admin/users/", views.AdminUserListView.as_view()),
    path("admin/cards/", views.AdminCardListView.as_view()),
    path("admin/transactions/", views.AdminTransactionListView.as_view()),
    path("admin/transactions/export/", views.AdminExportCSVView.as_view()),
    path("admin/summary/", views.AdminDailySummaryView.as_view()),
]