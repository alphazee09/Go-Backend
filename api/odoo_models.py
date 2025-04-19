from django.db import models
from .models import Integration, IntegrationTag

class OdooIntegration(models.Model):
    integration = models.OneToOneField(Integration, on_delete=models.CASCADE, related_name='odoo_config')
    url = models.URLField(verbose_name="Odoo Server URL")
    database = models.CharField(max_length=100, verbose_name="Database Name")
    username = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255, verbose_name="API Key/Password")
    company_id = models.IntegerField(default=1, verbose_name="Odoo Company ID")
    version = models.CharField(max_length=10, default="16.0", verbose_name="Odoo Version")
    
    # Sync settings
    sync_products = models.BooleanField(default=True, verbose_name="Sync Products")
    sync_customers = models.BooleanField(default=True, verbose_name="Sync Customers")
    sync_orders = models.BooleanField(default=True, verbose_name="Sync Orders")
    sync_invoices = models.BooleanField(default=True, verbose_name="Sync Invoices")
    
    # Sync intervals in minutes
    product_sync_interval = models.IntegerField(default=60, verbose_name="Product Sync Interval (minutes)")
    customer_sync_interval = models.IntegerField(default=60, verbose_name="Customer Sync Interval (minutes)")
    order_sync_interval = models.IntegerField(default=30, verbose_name="Order Sync Interval (minutes)")
    invoice_sync_interval = models.IntegerField(default=30, verbose_name="Invoice Sync Interval (minutes)")
    
    # Last sync timestamps
    last_product_sync = models.DateTimeField(null=True, blank=True)
    last_customer_sync = models.DateTimeField(null=True, blank=True)
    last_order_sync = models.DateTimeField(null=True, blank=True)
    last_invoice_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Odoo Integration"
        verbose_name_plural = "Odoo Integrations"
    
    def __str__(self):
        return f"Odoo Integration - {self.integration.name}"

class OdooProductMapping(models.Model):
    odoo_integration = models.ForeignKey(OdooIntegration, on_delete=models.CASCADE, related_name='product_mappings')
    go4rent_product_id = models.IntegerField(verbose_name="Go4Rent Product ID")
    odoo_product_id = models.IntegerField(verbose_name="Odoo Product ID")
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('odoo_integration', 'go4rent_product_id')
        verbose_name = "Odoo Product Mapping"
        verbose_name_plural = "Odoo Product Mappings"
    
    def __str__(self):
        return f"Product Mapping: {self.go4rent_product_id} -> {self.odoo_product_id}"

class OdooCustomerMapping(models.Model):
    odoo_integration = models.ForeignKey(OdooIntegration, on_delete=models.CASCADE, related_name='customer_mappings')
    go4rent_user_id = models.IntegerField(verbose_name="Go4Rent User ID")
    odoo_partner_id = models.IntegerField(verbose_name="Odoo Partner ID")
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('odoo_integration', 'go4rent_user_id')
        verbose_name = "Odoo Customer Mapping"
        verbose_name_plural = "Odoo Customer Mappings"
    
    def __str__(self):
        return f"Customer Mapping: {self.go4rent_user_id} -> {self.odoo_partner_id}"

class OdooOrderMapping(models.Model):
    odoo_integration = models.ForeignKey(OdooIntegration, on_delete=models.CASCADE, related_name='order_mappings')
    go4rent_order_id = models.IntegerField(verbose_name="Go4Rent Order ID")
    odoo_sale_order_id = models.IntegerField(verbose_name="Odoo Sale Order ID")
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('odoo_integration', 'go4rent_order_id')
        verbose_name = "Odoo Order Mapping"
        verbose_name_plural = "Odoo Order Mappings"
    
    def __str__(self):
        return f"Order Mapping: {self.go4rent_order_id} -> {self.odoo_sale_order_id}"

class OdooInvoiceMapping(models.Model):
    odoo_integration = models.ForeignKey(OdooIntegration, on_delete=models.CASCADE, related_name='invoice_mappings')
    go4rent_invoice_id = models.IntegerField(verbose_name="Go4Rent Invoice ID")
    odoo_invoice_id = models.IntegerField(verbose_name="Odoo Invoice ID")
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('odoo_integration', 'go4rent_invoice_id')
        verbose_name = "Odoo Invoice Mapping"
        verbose_name_plural = "Odoo Invoice Mappings"
    
    def __str__(self):
        return f"Invoice Mapping: {self.go4rent_invoice_id} -> {self.odoo_invoice_id}"

class OdooSyncLog(models.Model):
    SYNC_TYPES = (
        ('product', 'Product'),
        ('customer', 'Customer'),
        ('order', 'Order'),
        ('invoice', 'Invoice'),
    )
    
    SYNC_DIRECTIONS = (
        ('import', 'Import from Odoo'),
        ('export', 'Export to Odoo'),
    )
    
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('error', 'Error'),
        ('partial', 'Partial Success'),
    )
    
    odoo_integration = models.ForeignKey(OdooIntegration, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    direction = models.CharField(max_length=10, choices=SYNC_DIRECTIONS)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    records_processed = models.IntegerField(default=0)
    records_succeeded = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Odoo Sync Log"
        verbose_name_plural = "Odoo Sync Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_sync_type_display()} {self.get_direction_display()} - {self.timestamp}"
