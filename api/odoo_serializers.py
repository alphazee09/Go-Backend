from rest_framework import serializers
from ..odoo_models import (
    OdooIntegration, OdooProductMapping, OdooCustomerMapping, 
    OdooOrderMapping, OdooInvoiceMapping, OdooSyncLog
)

class OdooIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdooIntegration
        fields = [
            'id', 'integration', 'url', 'database', 'username', 'api_key',
            'company_id', 'version', 'sync_products', 'sync_customers',
            'sync_orders', 'sync_invoices', 'product_sync_interval',
            'customer_sync_interval', 'order_sync_interval', 'invoice_sync_interval',
            'last_product_sync', 'last_customer_sync', 'last_order_sync',
            'last_invoice_sync'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True}
        }

class OdooProductMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdooProductMapping
        fields = ['id', 'odoo_integration', 'go4rent_product_id', 'odoo_product_id', 'last_sync']

class OdooCustomerMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdooCustomerMapping
        fields = ['id', 'odoo_integration', 'go4rent_user_id', 'odoo_partner_id', 'last_sync']

class OdooOrderMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdooOrderMapping
        fields = ['id', 'odoo_integration', 'go4rent_order_id', 'odoo_sale_order_id', 'last_sync']

class OdooInvoiceMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdooInvoiceMapping
        fields = ['id', 'odoo_integration', 'go4rent_invoice_id', 'odoo_invoice_id', 'last_sync']

class OdooSyncLogSerializer(serializers.ModelSerializer):
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OdooSyncLog
        fields = [
            'id', 'odoo_integration', 'sync_type', 'sync_type_display',
            'direction', 'direction_display', 'status', 'status_display',
            'timestamp', 'records_processed', 'records_succeeded',
            'records_failed', 'error_message', 'details'
        ]
