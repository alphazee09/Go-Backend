from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .odoo_views import OdooIntegrationViewSet, OdooSyncLogViewSet

router = DefaultRouter()
router.register(r'odoo-integrations', OdooIntegrationViewSet)
router.register(r'odoo-sync-logs', OdooSyncLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
