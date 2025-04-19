from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import (
    Order, OrderItem, OrderTimeline,
    Product, MaintenanceRecord,
    Transaction, TransactionTimeline,
    Invoice, InvoiceItem
)

User = get_user_model()

# Create auth token for new users
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# Update product stock levels when order status changes
@receiver(post_save, sender=Order)
def update_product_stock(sender, instance=None, created=False, **kwargs):
    if not created and instance.status in ['confirmed', 'in_progress']:
        # When order is confirmed or in progress, update product availability
        order_items = OrderItem.objects.filter(order=instance)
        for item in order_items:
            product = item.product
            if instance.status == 'confirmed':
                # Reserve the products
                product.available_for_rent = max(0, product.available_for_rent - item.quantity)
                product.save()
            elif instance.status == 'in_progress':
                # Mark as rented
                product.currently_rented = product.currently_rented + item.quantity
                product.save()
    
    elif not created and instance.status == 'completed':
        # When order is completed, return products to available stock
        order_items = OrderItem.objects.filter(order=instance)
        for item in order_items:
            product = item.product
            product.currently_rented = max(0, product.currently_rented - item.quantity)
            product.available_for_rent = product.available_for_rent + item.quantity
            product.save()

# Create order timeline events when order status changes
@receiver(post_save, sender=Order)
def create_order_timeline(sender, instance=None, created=False, **kwargs):
    from django.utils import timezone
    
    if created:
        # Create initial timeline event
        OrderTimeline.objects.create(
            order=instance,
            type='order_created',
            date=timezone.now(),
            description='Order was created',
            user=instance.customer.get_full_name()
        )
    else:
        # Create timeline event for status changes
        status_descriptions = {
            'pending': 'Order is pending confirmation',
            'confirmed': 'Order was confirmed',
            'in_progress': 'Rental period started',
            'completed': 'Rental completed',
            'cancelled': 'Order was cancelled'
        }
        
        if instance.status in status_descriptions:
            OrderTimeline.objects.create(
                order=instance,
                type=f'order_{instance.status}',
                date=timezone.now(),
                description=status_descriptions[instance.status],
                user='System'
            )

# Update product maintenance status
@receiver(post_save, sender=MaintenanceRecord)
def update_maintenance_status(sender, instance=None, created=False, **kwargs):
    product = instance.product
    
    # Count active maintenance records
    active_maintenance = MaintenanceRecord.objects.filter(
        product=product, 
        status__in=['scheduled', 'in_progress']
    ).count()
    
    # Update product maintenance count
    product.under_maintenance = active_maintenance
    
    # Update available count
    product.available_for_rent = max(0, product.stock - product.currently_rented - product.under_maintenance)
    product.save()

# Create transaction timeline events
@receiver(post_save, sender=Transaction)
def create_transaction_timeline(sender, instance=None, created=False, **kwargs):
    from django.utils import timezone
    
    if created:
        # Create initial timeline event
        TransactionTimeline.objects.create(
            transaction=instance,
            title='Transaction Initiated',
            timestamp=timezone.now(),
            description=f'{instance.type} transaction initiated'
        )
    else:
        # Create timeline event for status changes
        status_titles = {
            'pending': 'Transaction Processing',
            'completed': 'Transaction Completed',
            'failed': 'Transaction Failed'
        }
        
        if instance.status in status_titles:
            TransactionTimeline.objects.create(
                transaction=instance,
                title=status_titles[instance.status],
                timestamp=timezone.now(),
                description=f'{instance.type} transaction {instance.status}'
            )

# Update invoice status when payment is received
@receiver(post_save, sender=Transaction)
def update_invoice_status(sender, instance=None, created=False, **kwargs):
    if instance.invoice and instance.status == 'completed':
        invoice = instance.invoice
        
        if instance.type == 'payment':
            # Add payment to invoice
            invoice.paid_amount += instance.amount
            
            # Update status based on payment
            if invoice.paid_amount >= invoice.amount:
                invoice.status = 'paid'
            else:
                invoice.status = 'partial'
                
        elif instance.type == 'refund':
            # Subtract refund from paid amount
            invoice.paid_amount = max(0, invoice.paid_amount - abs(instance.amount))
            
            # Update status based on remaining payment
            if invoice.paid_amount <= 0:
                invoice.status = 'refunded'
            else:
                invoice.status = 'partial_refund'
        
        invoice.save()
