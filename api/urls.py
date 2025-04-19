from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, CategoryViewSet, WarehouseViewSet, ProductViewSet,
    OrderViewSet, TransactionViewSet, InvoiceViewSet, ReportViewSet,
    CompanySettingsViewSet, RoleViewSet, NotificationSettingViewSet,
    IntegrationViewSet
)
from .dashboard import (
    DashboardStatsView, InventoryStatsView, FinancialStatsView,
    CustomerStatsView, GenerateReportView, SearchView
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'company-settings', CompanySettingsViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'notification-settings', NotificationSettingViewSet)
router.register(r'integrations', IntegrationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', include('api.dashboard_urls')),
    path('odoo/', include('api.odoo_urls')),  # Include Odoo URLs
]
