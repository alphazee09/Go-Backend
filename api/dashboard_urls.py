from django.urls import path
from . import dashboard

urlpatterns = [
    path('dashboard/stats/', dashboard.dashboard_stats, name='dashboard_stats'),
    path('dashboard/inventory/', dashboard.inventory_stats, name='inventory_stats'),
    path('dashboard/financial/', dashboard.financial_stats, name='financial_stats'),
    path('dashboard/customers/', dashboard.customer_stats, name='customer_stats'),
    path('dashboard/generate-report/', dashboard.generate_report, name='generate_report'),
    path('search/', dashboard.search, name='global_search'),
]
