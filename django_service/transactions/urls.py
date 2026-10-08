from django.urls import path

from cards import admin_views

from . import statement_views, views

urlpatterns = [
    path("transactions/", views.TransactionListView.as_view()),
    path("statements/", statement_views.MonthlyStatementView.as_view()),
    path("admin/users/", views.AdminUserListView.as_view()),
    path("admin/cards/", admin_views.AdminCardListView.as_view()),
    path("admin/cards/<int:pk>/block/", admin_views.AdminCardBlockView.as_view()),
    path("admin/cards/<int:pk>/unblock/", admin_views.AdminCardUnblockView.as_view()),
    path("admin/cards/<int:pk>/limit/", admin_views.AdminCardLimitView.as_view()),
    path("admin/cards/<int:pk>/activity/", admin_views.AdminCardActivityView.as_view()),
    path("admin/transactions/", views.AdminTransactionListView.as_view()),
    path("admin/transactions/export/", views.AdminExportCSVView.as_view()),
    path("admin/summary/", views.AdminDailySummaryView.as_view()),
]