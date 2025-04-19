from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
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
from .serializers import (
    # User serializers
    UserSerializer, UserCreateSerializer, UserDocumentSerializer, PaymentMethodSerializer,
    # Inventory serializers
    CategorySerializer, WarehouseSerializer, ProductSerializer, ProductSpecificationSerializer,
    ProductIncludedItemSerializer, ProductLocationSerializer, MaintenanceRecordSerializer,
    # Order serializers
    OrderSerializer, OrderItemSerializer, DeliveryAddressSerializer, RentalPeriodSerializer, OrderTimelineSerializer,
    # Finance serializers
    TransactionSerializer, TransactionTimelineSerializer, InvoiceSerializer, InvoiceItemSerializer, BillingAddressSerializer,
    # Report serializers
    ReportSerializer,
    # Settings serializers
    CompanySettingsSerializer, RoleSerializer, RolePermissionSerializer, NotificationSettingSerializer, IntegrationSerializer, IntegrationTagSerializer
)

User = get_user_model()

# Custom permission classes
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsManagerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'manager']

class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'manager', 'staff']

# Authentication
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'role': user.role,
            'name': user.get_full_name(),
        })

# User views
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'status']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_name', 'username']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsStaffUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        user = self.get_object()
        documents = UserDocument.objects.filter(user=user)
        serializer = UserDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payment_methods(self, request, pk=None):
        user = self.get_object()
        payment_methods = PaymentMethod.objects.filter(user=user)
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        return Response(serializer.data)

class UserDocumentViewSet(viewsets.ModelViewSet):
    queryset = UserDocument.objects.all()
    serializer_class = UserDocumentSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'verified']

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'type', 'is_default']

# Inventory views
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'location']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'rental_price', 'stock', 'added_date']
    
    @action(detail=True, methods=['get'])
    def specifications(self, request, pk=None):
        product = self.get_object()
        specs = ProductSpecification.objects.filter(product=product)
        serializer = ProductSpecificationSerializer(specs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def included_items(self, request, pk=None):
        product = self.get_object()
        items = ProductIncludedItem.objects.filter(product=product)
        serializer = ProductIncludedItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def locations(self, request, pk=None):
        product = self.get_object()
        locations = ProductLocation.objects.filter(product=product)
        serializer = ProductLocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def maintenance_records(self, request, pk=None):
        product = self.get_object()
        records = MaintenanceRecord.objects.filter(product=product)
        serializer = MaintenanceRecordSerializer(records, many=True)
        return Response(serializer.data)

class ProductSpecificationViewSet(viewsets.ModelViewSet):
    queryset = ProductSpecification.objects.all()
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

class ProductIncludedItemViewSet(viewsets.ModelViewSet):
    queryset = ProductIncludedItem.objects.all()
    serializer_class = ProductIncludedItemSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

class ProductLocationViewSet(viewsets.ModelViewSet):
    queryset = ProductLocation.objects.all()
    serializer_class = ProductLocationSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'warehouse']

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'status']
    ordering_fields = ['date']

# Order views
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status', 'payment_status']
    search_fields = ['id_code', 'customer__username', 'customer__email']
    ordering_fields = ['order_date', 'total_amount']
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        order = self.get_object()
        items = OrderItem.objects.filter(order=order)
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        order = self.get_object()
        timeline = OrderTimeline.objects.filter(order=order).order_by('date')
        serializer = OrderTimelineSerializer(timeline, many=True)
        return Response(serializer.data)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'product']

class DeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.all()
    serializer_class = DeliveryAddressSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order']

class RentalPeriodViewSet(viewsets.ModelViewSet):
    queryset = RentalPeriod.objects.all()
    serializer_class = RentalPeriodSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order']
    ordering_fields = ['start', 'end']

class OrderTimelineViewSet(viewsets.ModelViewSet):
    queryset = OrderTimeline.objects.all()
    serializer_class = OrderTimelineSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'type']
    ordering_fields = ['date']

# Finance views
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsManagerUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'type', 'status']
    search_fields = ['id_code', 'reference', 'customer__username', 'customer__email']
    ordering_fields = ['date', 'amount']
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        transaction = self.get_object()
        timeline = TransactionTimeline.objects.filter(transaction=transaction).order_by('timestamp')
        serializer = TransactionTimelineSerializer(timeline, many=True)
        return Response(serializer.data)

class TransactionTimelineViewSet(viewsets.ModelViewSet):
    queryset = TransactionTimeline.objects.all()
    serializer_class = TransactionTimelineSerializer
    permission_classes = [IsManagerUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction']
    ordering_fields = ['timestamp']

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsManagerUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status']
    search_fields = ['id_code', 'number', 'customer__username', 'customer__email']
    ordering_fields = ['issue_date', 'due_date', 'amount']
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        invoice = self.get_object()
        items = InvoiceItem.objects.filter(invoice=invoice)
        serializer = InvoiceItemSerializer(items, many=True)
        return Response(serializer.data)

class InvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsManagerUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice']

class BillingAddressViewSet(viewsets.ModelViewSet):
    queryset = BillingAddress.objects.all()
    serializer_class = BillingAddressSerializer
    permission_classes = [IsManagerUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice']

# Report views
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsManagerUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'created_by']
    search_fields = ['name', 'id_code']
    ordering_fields = ['date']

# Settings views
class CompanySettingsViewSet(viewsets.ModelViewSet):
    queryset = CompanySettings.objects.all()
    serializer_class = CompanySettingsSerializer
    permission_classes = [IsAdminUser]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        role = self.get_object()
        permissions = RolePermission.objects.filter(role=role)
        serializer = RolePermissionSerializer(permissions, many=True)
        return Response(serializer.data)

class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role']

class NotificationSettingViewSet(viewsets.ModelViewSet):
    queryset = NotificationSetting.objects.all()
    serializer_class = NotificationSettingSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']

class IntegrationViewSet(viewsets.ModelViewSet):
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def tags(self, request, pk=None):
        integration = self.get_object()
        tags = IntegrationTag.objects.filter(integration=integration)
        serializer = IntegrationTagSerializer(tags, many=True)
        return Response(serializer.data)

class IntegrationTagViewSet(viewsets.ModelViewSet):
    queryset = IntegrationTag.objects.all()
    serializer_class = IntegrationTagSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['integration']
