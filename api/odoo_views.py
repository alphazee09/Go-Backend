from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from ..odoo_models import (
    OdooIntegration, OdooProductMapping, OdooCustomerMapping, 
    OdooOrderMapping, OdooInvoiceMapping, OdooSyncLog
)
from ..odoo_serializers import (
    OdooIntegrationSerializer, OdooProductMappingSerializer, 
    OdooCustomerMappingSerializer, OdooOrderMappingSerializer,
    OdooInvoiceMappingSerializer, OdooSyncLogSerializer
)
from ..services.odoo_service import OdooSyncService
from ..models import Integration

class OdooIntegrationViewSet(viewsets.ModelViewSet):
    queryset = OdooIntegration.objects.all()
    serializer_class = OdooIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Create a base Integration record first
        with transaction.atomic():
            integration_data = {
                'name': request.data.get('name', 'Odoo Integration'),
                'type': 'odoo',
                'status': 'active',
                'description': request.data.get('description', 'Odoo ERP Integration')
            }
            integration = Integration.objects.create(**integration_data)
            
            # Add integration ID to request data
            request.data['integration'] = integration.id
            
            # Create OdooIntegration record
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test the connection to Odoo"""
        integration = self.get_object()
        
        try:
            # Initialize the sync service which tests the connection
            sync_service = OdooSyncService(integration.id)
            
            if sync_service.client.is_connected:
                return Response({
                    'success': True,
                    'message': 'Successfully connected to Odoo',
                    'details': {
                        'url': integration.url,
                        'database': integration.database,
                        'username': integration.username,
                        'company_id': integration.company_id,
                        'version': integration.version
                    }
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to connect to Odoo',
                    'error': 'Authentication failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to connect to Odoo',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_products(self, request, pk=None):
        """Sync products with Odoo"""
        integration = self.get_object()
        direction = request.data.get('direction', 'export')
        
        try:
            sync_service = OdooSyncService(integration.id)
            log = sync_service.sync_products(direction=direction)
            
            serializer = OdooSyncLogSerializer(log)
            return Response({
                'success': True,
                'message': f'Product sync {direction} completed',
                'log': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Product sync {direction} failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_customers(self, request, pk=None):
        """Sync customers with Odoo"""
        integration = self.get_object()
        direction = request.data.get('direction', 'export')
        
        try:
            sync_service = OdooSyncService(integration.id)
            log = sync_service.sync_customers(direction=direction)
            
            serializer = OdooSyncLogSerializer(log)
            return Response({
                'success': True,
                'message': f'Customer sync {direction} completed',
                'log': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Customer sync {direction} failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_orders(self, request, pk=None):
        """Sync orders with Odoo"""
        integration = self.get_object()
        direction = request.data.get('direction', 'export')
        
        try:
            sync_service = OdooSyncService(integration.id)
            log = sync_service.sync_orders(direction=direction)
            
            serializer = OdooSyncLogSerializer(log)
            return Response({
                'success': True,
                'message': f'Order sync {direction} completed',
                'log': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Order sync {direction} failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_invoices(self, request, pk=None):
        """Sync invoices with Odoo"""
        integration = self.get_object()
        direction = request.data.get('direction', 'export')
        
        try:
            sync_service = OdooSyncService(integration.id)
            log = sync_service.sync_invoices(direction=direction)
            
            serializer = OdooSyncLogSerializer(log)
            return Response({
                'success': True,
                'message': f'Invoice sync {direction} completed',
                'log': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Invoice sync {direction} failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_all(self, request, pk=None):
        """Sync all data with Odoo"""
        integration = self.get_object()
        direction = request.data.get('direction', 'export')
        
        try:
            sync_service = OdooSyncService(integration.id)
            logs = []
            
            if integration.sync_products:
                logs.append(sync_service.sync_products(direction=direction))
            
            if integration.sync_customers:
                logs.append(sync_service.sync_customers(direction=direction))
            
            if integration.sync_orders:
                logs.append(sync_service.sync_orders(direction=direction))
            
            if integration.sync_invoices:
                logs.append(sync_service.sync_invoices(direction=direction))
            
            serializer = OdooSyncLogSerializer(logs, many=True)
            return Response({
                'success': True,
                'message': f'All sync {direction} completed',
                'logs': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'All sync {direction} failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class OdooSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OdooSyncLog.objects.all().order_by('-timestamp')
    serializer_class = OdooSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by integration
        integration_id = self.request.query_params.get('integration')
        if integration_id:
            queryset = queryset.filter(odoo_integration_id=integration_id)
        
        # Filter by sync type
        sync_type = self.request.query_params.get('sync_type')
        if sync_type:
            queryset = queryset.filter(sync_type=sync_type)
        
        # Filter by direction
        direction = self.request.query_params.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset
