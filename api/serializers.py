from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import (
    # User related models
    UserDocument, PaymentMethod,
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

User = get_user_model()

# User Serializers
class UserDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocument
        fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    documents = UserDocumentSerializer(many=True, read_only=True)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                 'address', 'role', 'status', 'avatar', 'last_active', 
                 'loyalty_points', 'date_joined', 'documents', 'payment_methods']
        read_only_fields = ['id', 'date_joined', 'last_active']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 
                 'phone', 'address', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

# Inventory Serializers
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = '__all__'

class ProductIncludedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductIncludedItem
        fields = '__all__'

class ProductLocationSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    
    class Meta:
        model = ProductLocation
        fields = '__all__'

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    included_items = ProductIncludedItemSerializer(many=True, read_only=True)
    locations = ProductLocationSerializer(many=True, read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

# Order Serializers
class DeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = '__all__'

class RentalPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalPeriod
        fields = '__all__'

class OrderTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTimeline
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.get_full_name')
    customer_email = serializers.ReadOnlyField(source='customer.email')
    items = OrderItemSerializer(many=True, read_only=True)
    delivery_address = DeliveryAddressSerializer(read_only=True)
    rental_period = RentalPeriodSerializer(read_only=True)
    timeline = OrderTimelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

# Finance Serializers
class TransactionTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionTimeline
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.get_full_name')
    timeline = TransactionTimelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'

class BillingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingAddress
        fields = '__all__'

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.get_full_name')
    customer_email = serializers.ReadOnlyField(source='customer.email')
    items = InvoiceItemSerializer(many=True, read_only=True)
    billing_address = BillingAddressSerializer(read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'

# Report Serializers
class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = Report
        fields = '__all__'

# Settings Serializers
class CompanySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySettings
        fields = '__all__'

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    permissions = RolePermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = '__all__'

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = '__all__'

class IntegrationTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationTag
        fields = '__all__'

class IntegrationSerializer(serializers.ModelSerializer):
    tags = IntegrationTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Integration
        fields = '__all__'
