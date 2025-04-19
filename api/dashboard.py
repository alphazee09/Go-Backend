from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Product, Order, Transaction, Invoice, Report,
    User, MaintenanceRecord
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get summary statistics for the dashboard
    """
    # Get counts
    total_products = Product.objects.count()
    available_products = Product.objects.filter(available_for_rent__gt=0).count()
    total_orders = Order.objects.count()
    active_orders = Order.objects.filter(status__in=['confirmed', 'in_progress']).count()
    
    # Get financial summary
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Monthly revenue
    monthly_revenue = Transaction.objects.filter(
        type='payment',
        status='completed',
        date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending payments
    pending_payments = Invoice.objects.filter(
        status__in=['sent', 'overdue']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent activity
    recent_orders = Order.objects.order_by('-order_date')[:5]
    recent_transactions = Transaction.objects.order_by('-date', '-time')[:5]
    
    return Response({
        'counts': {
            'total_products': total_products,
            'available_products': available_products,
            'total_orders': total_orders,
            'active_orders': active_orders,
        },
        'financial': {
            'monthly_revenue': monthly_revenue,
            'pending_payments': pending_payments,
        },
        'recent_activity': {
            'orders': [
                {
                    'id': order.id_code,
                    'customer': order.customer.get_full_name(),
                    'date': order.order_date,
                    'status': order.status,
                    'amount': order.total_amount
                } for order in recent_orders
            ],
            'transactions': [
                {
                    'id': tx.id_code,
                    'customer': tx.customer.get_full_name(),
                    'date': tx.date,
                    'type': tx.type,
                    'amount': tx.amount,
                    'status': tx.status
                } for tx in recent_transactions
            ]
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_stats(request):
    """
    Get inventory statistics
    """
    # Stock levels by category
    categories = Product.objects.values('category__name').annotate(
        total=Count('id'),
        available=Sum('available_for_rent'),
        rented=Sum('currently_rented'),
        maintenance=Sum('under_maintenance')
    ).order_by('category__name')
    
    # Low stock alerts
    low_stock = Product.objects.filter(
        available_for_rent__lt=F('min_stock_level')
    ).values('id_code', 'name', 'available_for_rent', 'min_stock_level')
    
    # Maintenance status
    maintenance_status = MaintenanceRecord.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Utilization rate (percentage of products currently rented)
    total_products = Product.objects.aggregate(
        total=Sum('stock'),
        rented=Sum('currently_rented')
    )
    
    utilization_rate = 0
    if total_products['total'] and total_products['total'] > 0:
        utilization_rate = (total_products['rented'] or 0) / total_products['total'] * 100
    
    return Response({
        'categories': categories,
        'low_stock_alerts': low_stock,
        'maintenance': maintenance_status,
        'utilization_rate': utilization_rate
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_stats(request):
    """
    Get financial statistics
    """
    # Get date ranges
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    # Monthly revenue breakdown
    monthly_revenue = Transaction.objects.filter(
        type='payment',
        status='completed',
        date__gte=month_start
    ).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Revenue by product category
    category_revenue = OrderItem.objects.filter(
        order__status='completed'
    ).values('product__category__name').annotate(
        total=Sum(F('price') * F('quantity'))
    ).order_by('-total')
    
    # Outstanding invoices
    outstanding_invoices = Invoice.objects.filter(
        status__in=['sent', 'overdue']
    ).aggregate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    # Year-to-date summary
    ytd_summary = Transaction.objects.filter(
        date__gte=year_start
    ).values('type').annotate(
        total=Sum('amount')
    )
    
    return Response({
        'monthly_revenue': monthly_revenue,
        'category_revenue': category_revenue,
        'outstanding_invoices': outstanding_invoices,
        'ytd_summary': ytd_summary
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_stats(request):
    """
    Get customer statistics
    """
    # Top customers by revenue
    top_customers = Order.objects.filter(
        status='completed'
    ).values('customer__id', 'customer__first_name', 'customer__last_name').annotate(
        total_spent=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('-total_spent')[:10]
    
    # New customers this month
    month_start = timezone.now().date().replace(day=1)
    new_customers = User.objects.filter(
        role='customer',
        date_joined__gte=month_start
    ).count()
    
    # Customer retention (customers who made orders in consecutive months)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    
    last_month_customers = Order.objects.filter(
        order_date__gte=last_month_start,
        order_date__lt=month_start
    ).values_list('customer_id', flat=True).distinct()
    
    this_month_returning = Order.objects.filter(
        order_date__gte=month_start,
        customer_id__in=last_month_customers
    ).values_list('customer_id', flat=True).distinct().count()
    
    retention_rate = 0
    if len(last_month_customers) > 0:
        retention_rate = (this_month_returning / len(last_month_customers)) * 100
    
    return Response({
        'top_customers': top_customers,
        'new_customers': new_customers,
        'retention_rate': retention_rate
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report(request):
    """
    Generate a new report
    """
    report_type = request.data.get('type')
    name = request.data.get('name')
    
    if not report_type or not name:
        return Response(
            {'error': 'Report type and name are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create a new report record
    report = Report.objects.create(
        id_code=f"REP-{Report.objects.count() + 1:03d}",
        name=name,
        type=report_type,
        date=timezone.now().date(),
        status='processing',
        created_by=request.user
    )
    
    # In a real implementation, this would trigger a background task
    # to generate the actual report file
    
    return Response({
        'id': report.id_code,
        'name': report.name,
        'type': report.type,
        'status': report.status,
        'message': 'Report generation started'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search(request):
    """
    Global search across multiple models
    """
    query = request.query_params.get('q', '')
    if not query or len(query) < 3:
        return Response(
            {'error': 'Search query must be at least 3 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Search products
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(sku__icontains=query) |
        Q(description__icontains=query)
    )[:5]
    
    # Search orders
    orders = Order.objects.filter(
        Q(id_code__icontains=query) |
        Q(customer__first_name__icontains=query) |
        Q(customer__last_name__icontains=query) |
        Q(customer__email__icontains=query)
    )[:5]
    
    # Search users
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:5]
    
    # Search invoices
    invoices = Invoice.objects.filter(
        Q(id_code__icontains=query) |
        Q(number__icontains=query)
    )[:5]
    
    return Response({
        'products': [
            {
                'id': p.id_code,
                'name': p.name,
                'type': 'product',
                'url': f'/inventory/products/{p.id}'
            } for p in products
        ],
        'orders': [
            {
                'id': o.id_code,
                'name': f"Order {o.id_code} - {o.customer.get_full_name()}",
                'type': 'order',
                'url': f'/orders/{o.id}'
            } for o in orders
        ],
        'users': [
            {
                'id': u.id,
                'name': u.get_full_name() or u.username,
                'type': 'user',
                'url': f'/users/{u.id}'
            } for u in users
        ],
        'invoices': [
            {
                'id': i.id_code,
                'name': f"Invoice {i.number}",
                'type': 'invoice',
                'url': f'/finance/invoices/{i.id}'
            } for i in invoices
        ]
    })
