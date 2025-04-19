from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# User Models
class User(AbstractUser):
    """Extended User model with additional fields for Go4Rent"""
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
        ('viewer', 'Viewer'),
    ], default='customer')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    last_active = models.DateTimeField(blank=True, null=True)
    loyalty_points = models.IntegerField(default=0)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name='go4rent_users',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name='go4rent_users',
        related_query_name='user',
    )
    
    def __str__(self):
        return self.username

class UserDocument(models.Model):
    """Documents uploaded by users (ID, licenses, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=100)
    document = models.FileField(upload_to='user_documents/')
    upload_date = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

class PaymentMethod(models.Model):
    """Payment methods saved by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=50)
    last4 = models.CharField(max_length=4)
    expiry = models.CharField(max_length=7, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type} **** {self.last4} - {self.user.username}"

# Inventory Models
class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Warehouse(models.Model):
    """Warehouses where products are stored"""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    address = models.TextField()
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Products available for rent"""
    id_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    rental_price = models.DecimalField(max_digits=10, decimal_places=2)
    replacement_value = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=0)
    max_stock_level = models.IntegerField(default=0)
    available_for_rent = models.IntegerField(default=0)
    currently_rented = models.IntegerField(default=0)
    under_maintenance = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ], default='active')
    added_date = models.DateField(auto_now_add=True)
    last_restocked = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class ProductSpecification(models.Model):
    """Technical specifications for products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.name}: {self.value}"

class ProductIncludedItem(models.Model):
    """Items included with a product rental"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='included_items')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class ProductLocation(models.Model):
    """Physical location of products in warehouse"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='locations')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    section = models.CharField(max_length=20)
    shelf = models.CharField(max_length=20)
    bin = models.CharField(max_length=20)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.warehouse.name} - {self.section}{self.shelf}{self.bin}"

class MaintenanceRecord(models.Model):
    """Maintenance records for products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='maintenance_records')
    type = models.CharField(max_length=50)
    date = models.DateField()
    technician = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ])
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.type} - {self.date}"

# Order Models
class Order(models.Model):
    """Customer orders/rentals"""
    id_code = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ], default='pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.id_code

class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    duration = models.IntegerField(help_text="Duration in days")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    device_id = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

class DeliveryAddress(models.Model):
    """Delivery addresses for orders"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_address')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    
    class Meta:
        verbose_name_plural = "Delivery addresses"
    
    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

class RentalPeriod(models.Model):
    """Rental period for an order"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='rental_period')
    start = models.DateTimeField()
    end = models.DateTimeField()
    
    def __str__(self):
        return f"{self.start.date()} to {self.end.date()}"

class OrderTimeline(models.Model):
    """Timeline events for an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='timeline')
    type = models.CharField(max_length=50)
    date = models.DateTimeField()
    description = models.CharField(max_length=255)
    user = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.order.id_code} - {self.type} - {self.date}"

# Finance Models
class Transaction(models.Model):
    """Financial transactions"""
    id_code = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=[
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('deposit', 'Deposit'),
        ('adjustment', 'Adjustment'),
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    card_type = models.CharField(max_length=50, blank=True, null=True)
    last4 = models.CharField(max_length=4, blank=True, null=True)
    processor = models.CharField(max_length=50, blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    date = models.DateField()
    time = models.TimeField()
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.id_code

class TransactionTimeline(models.Model):
    """Timeline events for a transaction"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='timeline')
    title = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    description = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.transaction.id_code} - {self.title}"

class Invoice(models.Model):
    """Invoices for orders"""
    id_code = models.CharField(max_length=20, unique=True)
    number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    issue_date = models.DateField()
    due_date = models.DateField()
    payment_terms = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ], default='draft')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.number

class InvoiceItem(models.Model):
    """Individual items in an invoice"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} - {self.invoice.number}"

class BillingAddress(models.Model):
    """Billing addresses for invoices"""
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='billing_address')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    
    class Meta:
        verbose_name_plural = "Billing addresses"
    
    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

# Report Models
class Report(models.Model):
    """Generated reports"""
    id_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports')
    
    def __str__(self):
        return self.name

# Settings Models
class CompanySettings(models.Model):
    """Company settings"""
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    timezone = models.CharField(max_length=50, default='America/Los_Angeles')
    date_format = models.CharField(max_length=20, default='MM/DD/YYYY')
    currency = models.CharField(max_length=3, default='USD')
    
    class Meta:
        verbose_name_plural = "Company settings"
    
    def __str__(self):
        return self.company_name

class Role(models.Model):
    """User roles with permissions"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class RolePermission(models.Model):
    """Permissions for roles"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.role.name} - {self.permission}"

class NotificationSetting(models.Model):
    """Notification settings"""
    category = models.CharField(max_length=50)
    email = models.BooleanField(default=True)
    in_app = models.BooleanField(default=True)
    sms = models.BooleanField(default=False)
    
    def __str__(self):
        return self.category

class Integration(models.Model):
    """Third-party integrations"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('available', 'Available'),
    ], default='available')
    icon = models.CharField(max_length=50, blank=True, null=True)
    docs_url = models.URLField(blank=True, null=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class IntegrationTag(models.Model):
    """Tags for integrations"""
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
