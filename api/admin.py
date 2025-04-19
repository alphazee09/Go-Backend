from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    # User related models
    User, UserDocument, PaymentMethod,
    # Inventory related models
    Category, Warehouse, Product, ProductSpecification, 
    ProductIncludedItem, ProductLocation, MaintenanceRecord,
    # Order related models
    Order, OrderItem, DeliveryAddress, RentalPeriod, OrderTimeline,
    # Finance related models
    Transaction, TransactionTimeline, Invoice, InvoiceItem, BillingAddress,
    # Report models
    Report,
    # Settings models
    CompanySettings, Role, RolePermission, NotificationSetting, Integration, IntegrationTag
)

# User admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'status', 'is_staff')
    list_filter = ('role', 'status', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Go4Rent Info', {'fields': ('phone', 'address', 'role', 'status', 'avatar', 'last_active', 'loyalty_points')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Go4Rent Info', {'fields': ('phone', 'address', 'role', 'status')}),
    )

admin.site.register(User, CustomUserAdmin)

# User related models
admin.site.register(UserDocument)
admin.site.register(PaymentMethod)

# Inventory related models
admin.site.register(Category)
admin.site.register(Warehouse)

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

class ProductIncludedItemInline(admin.TabularInline):
    model = ProductIncludedItem
    extra = 1

class ProductLocationInline(admin.TabularInline):
    model = ProductLocation
    extra = 1

class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id_code', 'name', 'category', 'rental_price', 'stock', 'available_for_rent', 'status')
    list_filter = ('category', 'status')
    search_fields = ('name', 'sku', 'description')
    inlines = [
        ProductSpecificationInline,
        ProductIncludedItemInline,
        ProductLocationInline,
        MaintenanceRecordInline
    ]

admin.site.register(MaintenanceRecord)

# Order related models
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderTimelineInline(admin.TabularInline):
    model = OrderTimeline
    extra = 0
    readonly_fields = ('date',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id_code', 'customer', 'order_date', 'status', 'total_amount', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('id_code', 'customer__username', 'customer__email')
    inlines = [
        OrderItemInline,
        OrderTimelineInline
    ]

admin.site.register(DeliveryAddress)
admin.site.register(RentalPeriod)

# Finance related models
class TransactionTimelineInline(admin.TabularInline):
    model = TransactionTimeline
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id_code', 'customer', 'type', 'amount', 'status', 'date')
    list_filter = ('type', 'status')
    search_fields = ('id_code', 'customer__username', 'customer__email', 'reference')
    inlines = [
        TransactionTimelineInline
    ]

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id_code', 'number', 'customer', 'amount', 'status', 'issue_date', 'due_date')
    list_filter = ('status',)
    search_fields = ('id_code', 'number', 'customer__username', 'customer__email')
    inlines = [
        InvoiceItemInline
    ]

admin.site.register(BillingAddress)

# Report models
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id_code', 'name', 'type', 'date', 'status', 'created_by')
    list_filter = ('type', 'status')
    search_fields = ('name', 'id_code')

# Settings models
admin.site.register(CompanySettings)

class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [
        RolePermissionInline
    ]

admin.site.register(NotificationSetting)

class IntegrationTagInline(admin.TabularInline):
    model = IntegrationTag
    extra = 1

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'last_sync')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    inlines = [
        IntegrationTagInline
    ]
