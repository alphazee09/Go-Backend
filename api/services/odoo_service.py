import xmlrpc.client
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from ..models import Product, User, Order, OrderItem, Invoice, InvoiceItem
from ..odoo_models import (
    OdooIntegration, OdooProductMapping, OdooCustomerMapping, 
    OdooOrderMapping, OdooInvoiceMapping, OdooSyncLog
)

logger = logging.getLogger(__name__)

class OdooClient:
    """
    Client for interacting with Odoo API using XML-RPC
    """
    
    def __init__(self, integration_id):
        """
        Initialize the Odoo client with integration settings
        
        Args:
            integration_id: ID of the OdooIntegration record
        """
        try:
            self.integration = OdooIntegration.objects.get(id=integration_id)
            self.url = self.integration.url
            self.db = self.integration.database
            self.username = self.integration.username
            self.api_key = self.integration.api_key
            self.company_id = self.integration.company_id
            
            # Set up XML-RPC endpoints
            self.common_endpoint = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.object_endpoint = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            # Authenticate and get user ID
            self.uid = self.common_endpoint.authenticate(self.db, self.username, self.api_key, {})
            
            if not self.uid:
                raise Exception("Authentication with Odoo failed")
                
            self.is_connected = True
            logger.info(f"Successfully connected to Odoo at {self.url}")
            
        except OdooIntegration.DoesNotExist:
            logger.error(f"Odoo integration with ID {integration_id} not found")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error initializing Odoo client: {str(e)}")
            self.is_connected = False
    
    def execute_kw(self, model, method, args=None, kwargs=None):
        """
        Execute a method on an Odoo model
        
        Args:
            model: Odoo model name
            method: Method to call
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Result from Odoo API
        """
        if not self.is_connected:
            raise Exception("Not connected to Odoo")
            
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        try:
            result = self.object_endpoint.execute_kw(
                self.db, self.uid, self.api_key,
                model, method, args, kwargs
            )
            return result
        except Exception as e:
            logger.error(f"Error executing {method} on {model}: {str(e)}")
            raise
    
    def search_read(self, model, domain=None, fields=None, limit=None, offset=0, order=None):
        """
        Search and read records from an Odoo model
        
        Args:
            model: Odoo model name
            domain: Search domain
            fields: Fields to return
            limit: Maximum number of records
            offset: Offset for pagination
            order: Order by clause
            
        Returns:
            List of records
        """
        if domain is None:
            domain = []
        if fields is None:
            fields = []
            
        kwargs = {
            'domain': domain,
            'fields': fields,
        }
        
        if limit is not None:
            kwargs['limit'] = limit
        if offset:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
            
        return self.execute_kw(model, 'search_read', [[]], kwargs)
    
    def create(self, model, values):
        """
        Create a record in an Odoo model
        
        Args:
            model: Odoo model name
            values: Values for the new record
            
        Returns:
            ID of the created record
        """
        return self.execute_kw(model, 'create', [[values]])
    
    def write(self, model, ids, values):
        """
        Update records in an Odoo model
        
        Args:
            model: Odoo model name
            ids: IDs of records to update
            values: Values to update
            
        Returns:
            True if successful
        """
        return self.execute_kw(model, 'write', [ids, values])
    
    def unlink(self, model, ids):
        """
        Delete records from an Odoo model
        
        Args:
            model: Odoo model name
            ids: IDs of records to delete
            
        Returns:
            True if successful
        """
        return self.execute_kw(model, 'unlink', [ids])


class OdooSyncService:
    """
    Service for synchronizing data between Go4Rent and Odoo
    """
    
    def __init__(self, integration_id):
        """
        Initialize the sync service
        
        Args:
            integration_id: ID of the OdooIntegration record
        """
        self.integration_id = integration_id
        self.client = OdooClient(integration_id)
        self.integration = OdooIntegration.objects.get(id=integration_id)
    
    def sync_products(self, direction='export'):
        """
        Synchronize products between Go4Rent and Odoo
        
        Args:
            direction: 'import' or 'export'
            
        Returns:
            OdooSyncLog record
        """
        log = OdooSyncLog.objects.create(
            odoo_integration=self.integration,
            sync_type='product',
            direction=direction,
            status='success',
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            details={}
        )
        
        try:
            if direction == 'export':
                return self._export_products(log)
            else:
                return self._import_products(log)
        except Exception as e:
            log.status = 'error'
            log.error_message = str(e)
            log.save()
            logger.error(f"Error in product sync: {str(e)}")
            return log
    
    def _export_products(self, log):
        """
        Export products from Go4Rent to Odoo
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get products to export
        if self.integration.last_product_sync:
            products = Product.objects.filter(
                updated_at__gt=self.integration.last_product_sync
            )
        else:
            products = Product.objects.all()
        
        log.records_processed = products.count()
        details = {'exported': [], 'failed': []}
        
        for product in products:
            try:
                # Check if product already exists in Odoo
                mapping = OdooProductMapping.objects.filter(
                    odoo_integration=self.integration,
                    go4rent_product_id=product.id
                ).first()
                
                odoo_values = {
                    'name': product.name,
                    'default_code': product.sku,
                    'list_price': float(product.rental_price),
                    'standard_price': float(product.replacement_value),
                    'type': 'product',  # Storable product
                    'description': product.description,
                    'company_id': self.integration.company_id,
                    'x_go4rent_id': product.id,
                    'x_go4rent_id_code': product.id_code,
                }
                
                if mapping:
                    # Update existing product
                    self.client.write('product.template', [mapping.odoo_product_id], odoo_values)
                    odoo_id = mapping.odoo_product_id
                else:
                    # Create new product
                    odoo_id = self.client.create('product.template', odoo_values)
                    mapping = OdooProductMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_product_id=product.id,
                        odoo_product_id=odoo_id
                    )
                
                details['exported'].append({
                    'go4rent_id': product.id,
                    'go4rent_id_code': product.id_code,
                    'odoo_id': odoo_id,
                    'name': product.name
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'go4rent_id': product.id,
                    'go4rent_id_code': product.id_code,
                    'name': product.name,
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error exporting product {product.id_code}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_product_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def _import_products(self, log):
        """
        Import products from Odoo to Go4Rent
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get products from Odoo
        domain = []
        if self.integration.last_product_sync:
            # Convert timezone-aware datetime to string in Odoo format
            last_sync_str = self.integration.last_product_sync.strftime('%Y-%m-%d %H:%M:%S')
            domain.append(('write_date', '>', last_sync_str))
        
        odoo_products = self.client.search_read(
            'product.template',
            domain=domain,
            fields=['id', 'name', 'default_code', 'list_price', 'standard_price', 
                   'description', 'type', 'x_go4rent_id']
        )
        
        log.records_processed = len(odoo_products)
        details = {'imported': [], 'failed': []}
        
        for odoo_product in odoo_products:
            try:
                # Check if product already exists in Go4Rent
                mapping = None
                
                # Check if product has Go4Rent ID
                if odoo_product.get('x_go4rent_id'):
                    try:
                        product = Product.objects.get(id=odoo_product['x_go4rent_id'])
                        mapping = OdooProductMapping.objects.filter(
                            odoo_integration=self.integration,
                            go4rent_product_id=product.id
                        ).first()
                    except Product.DoesNotExist:
                        pass
                
                # If no mapping found, check by Odoo ID
                if not mapping:
                    mapping = OdooProductMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_product_id=odoo_product['id']
                    ).first()
                
                if mapping:
                    # Update existing product
                    product = Product.objects.get(id=mapping.go4rent_product_id)
                    product.name = odoo_product['name']
                    product.sku = odoo_product.get('default_code', '')
                    product.rental_price = odoo_product.get('list_price', 0)
                    product.replacement_value = odoo_product.get('standard_price', 0)
                    product.description = odoo_product.get('description', '')
                    product.save()
                else:
                    # Create new product
                    # Get or create a default category
                    from ..models import Category
                    category, _ = Category.objects.get_or_create(name="Imported from Odoo")
                    
                    # Generate a unique ID code
                    from ..models import Product
                    id_code = f"PRD-{Product.objects.count() + 1:03d}"
                    
                    product = Product.objects.create(
                        id_code=id_code,
                        name=odoo_product['name'],
                        sku=odoo_product.get('default_code', f"ODO-{odoo_product['id']}"),
                        category=category,
                        description=odoo_product.get('description', ''),
                        rental_price=odoo_product.get('list_price', 0),
                        replacement_value=odoo_product.get('standard_price', 0),
                        stock=0,
                        available_for_rent=0,
                        status='active'
                    )
                    
                    mapping = OdooProductMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_product_id=product.id,
                        odoo_product_id=odoo_product['id']
                    )
                
                details['imported'].append({
                    'odoo_id': odoo_product['id'],
                    'go4rent_id': product.id,
                    'go4rent_id_code': product.id_code,
                    'name': product.name
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'odoo_id': odoo_product['id'],
                    'name': odoo_product['name'],
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error importing product {odoo_product['id']}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_product_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def sync_customers(self, direction='export'):
        """
        Synchronize customers between Go4Rent and Odoo
        
        Args:
            direction: 'import' or 'export'
            
        Returns:
            OdooSyncLog record
        """
        log = OdooSyncLog.objects.create(
            odoo_integration=self.integration,
            sync_type='customer',
            direction=direction,
            status='success',
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            details={}
        )
        
        try:
            if direction == 'export':
                return self._export_customers(log)
            else:
                return self._import_customers(log)
        except Exception as e:
            log.status = 'error'
            log.error_message = str(e)
            log.save()
            logger.error(f"Error in customer sync: {str(e)}")
            return log
    
    def _export_customers(self, log):
        """
        Export customers from Go4Rent to Odoo
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get customers to export (only users with role='customer')
        if self.integration.last_customer_sync:
            customers = User.objects.filter(
                role='customer',
                date_joined__gt=self.integration.last_customer_sync
            )
        else:
            customers = User.objects.filter(role='customer')
        
        log.records_processed = customers.count()
        details = {'exported': [], 'failed': []}
        
        for customer in customers:
            try:
                # Check if customer already exists in Odoo
                mapping = OdooCustomerMapping.objects.filter(
                    odoo_integration=self.integration,
                    go4rent_user_id=customer.id
                ).first()
                
                odoo_values = {
                    'name': f"{customer.first_name} {customer.last_name}".strip(),
                    'email': customer.email,
                    'phone': customer.phone,
                    'street': customer.address,
                    'customer': True,
                    'company_id': self.integration.company_id,
                    'x_go4rent_id': customer.id,
                }
                
                if mapping:
                    # Update existing customer
                    self.client.write('res.partner', [mapping.odoo_partner_id], odoo_values)
                    odoo_id = mapping.odoo_partner_id
                else:
                    # Create new customer
                    odoo_id = self.client.create('res.partner', odoo_values)
                    mapping = OdooCustomerMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_user_id=customer.id,
                        odoo_partner_id=odoo_id
                    )
                
                details['exported'].append({
                    'go4rent_id': customer.id,
                    'odoo_id': odoo_id,
                    'name': f"{customer.first_name} {customer.last_name}".strip()
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'go4rent_id': customer.id,
                    'name': f"{customer.first_name} {customer.last_name}".strip(),
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error exporting customer {customer.id}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_customer_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def _import_customers(self, log):
        """
        Import customers from Odoo to Go4Rent
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get customers from Odoo
        domain = [('customer', '=', True)]
        if self.integration.last_customer_sync:
            # Convert timezone-aware datetime to string in Odoo format
            last_sync_str = self.integration.last_customer_sync.strftime('%Y-%m-%d %H:%M:%S')
            domain.append(('write_date', '>', last_sync_str))
        
        odoo_customers = self.client.search_read(
            'res.partner',
            domain=domain,
            fields=['id', 'name', 'email', 'phone', 'street', 'x_go4rent_id']
        )
        
        log.records_processed = len(odoo_customers)
        details = {'imported': [], 'failed': []}
        
        for odoo_customer in odoo_customers:
            try:
                # Check if customer already exists in Go4Rent
                mapping = None
                
                # Check if customer has Go4Rent ID
                if odoo_customer.get('x_go4rent_id'):
                    try:
                        customer = User.objects.get(id=odoo_customer['x_go4rent_id'])
                        mapping = OdooCustomerMapping.objects.filter(
                            odoo_integration=self.integration,
                            go4rent_user_id=customer.id
                        ).first()
                    except User.DoesNotExist:
                        pass
                
                # If no mapping found, check by Odoo ID
                if not mapping:
                    mapping = OdooCustomerMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_partner_id=odoo_customer['id']
                    ).first()
                
                # If still no mapping, check by email
                if not mapping and odoo_customer.get('email'):
                    try:
                        customer = User.objects.get(email=odoo_customer['email'])
                        mapping = OdooCustomerMapping.objects.filter(
                            odoo_integration=self.integration,
                            go4rent_user_id=customer.id
                        ).first()
                        
                        if not mapping:
                            mapping = OdooCustomerMapping.objects.create(
                                odoo_integration=self.integration,
                                go4rent_user_id=customer.id,
                                odoo_partner_id=odoo_customer['id']
                            )
                    except User.DoesNotExist:
                        pass
                
                if mapping:
                    # Update existing customer
                    customer = User.objects.get(id=mapping.go4rent_user_id)
                    
                    # Split name into first and last name
                    name_parts = odoo_customer['name'].split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    customer.first_name = first_name
                    customer.last_name = last_name
                    customer.email = odoo_customer.get('email', '')
                    customer.phone = odoo_customer.get('phone', '')
                    customer.address = odoo_customer.get('street', '')
                    customer.save()
                else:
                    # Create new customer
                    # Split name into first and last name
                    name_parts = odoo_customer['name'].split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # Generate username from email or name
                    username = odoo_customer.get('email', '').split('@')[0]
                    if not username:
                        username = odoo_customer['name'].lower().replace(' ', '_')
                    
                    # Make sure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    # Generate a random password
                    import random
                    import string
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                    
                    customer = User.objects.create_user(
                        username=username,
                        email=odoo_customer.get('email', ''),
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone=odoo_customer.get('phone', ''),
                        address=odoo_customer.get('street', ''),
                        role='customer',
                        status='active'
                    )
                    
                    mapping = OdooCustomerMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_user_id=customer.id,
                        odoo_partner_id=odoo_customer['id']
                    )
                
                details['imported'].append({
                    'odoo_id': odoo_customer['id'],
                    'go4rent_id': customer.id,
                    'name': odoo_customer['name']
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'odoo_id': odoo_customer['id'],
                    'name': odoo_customer['name'],
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error importing customer {odoo_customer['id']}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_customer_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def sync_orders(self, direction='export'):
        """
        Synchronize orders between Go4Rent and Odoo
        
        Args:
            direction: 'import' or 'export'
            
        Returns:
            OdooSyncLog record
        """
        log = OdooSyncLog.objects.create(
            odoo_integration=self.integration,
            sync_type='order',
            direction=direction,
            status='success',
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            details={}
        )
        
        try:
            if direction == 'export':
                return self._export_orders(log)
            else:
                return self._import_orders(log)
        except Exception as e:
            log.status = 'error'
            log.error_message = str(e)
            log.save()
            logger.error(f"Error in order sync: {str(e)}")
            return log
    
    def _export_orders(self, log):
        """
        Export orders from Go4Rent to Odoo
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get orders to export
        if self.integration.last_order_sync:
            orders = Order.objects.filter(
                updated_at__gt=self.integration.last_order_sync
            )
        else:
            orders = Order.objects.all()
        
        log.records_processed = orders.count()
        details = {'exported': [], 'failed': []}
        
        for order in orders:
            try:
                # Check if customer exists in Odoo
                customer_mapping = OdooCustomerMapping.objects.filter(
                    odoo_integration=self.integration,
                    go4rent_user_id=order.customer.id
                ).first()
                
                if not customer_mapping:
                    # Export customer first
                    customer_sync = OdooSyncService(self.integration_id)
                    customer_log = customer_sync.sync_customers(direction='export')
                    
                    # Try to get mapping again
                    customer_mapping = OdooCustomerMapping.objects.filter(
                        odoo_integration=self.integration,
                        go4rent_user_id=order.customer.id
                    ).first()
                    
                    if not customer_mapping:
                        raise Exception(f"Customer {order.customer.id} could not be exported to Odoo")
                
                # Check if order already exists in Odoo
                mapping = OdooOrderMapping.objects.filter(
                    odoo_integration=self.integration,
                    go4rent_order_id=order.id
                ).first()
                
                # Get order items
                order_items = OrderItem.objects.filter(order=order)
                
                # Map status to Odoo status
                status_map = {
                    'pending': 'draft',
                    'confirmed': 'sent',
                    'in_progress': 'sale',
                    'completed': 'done',
                    'cancelled': 'cancel'
                }
                
                odoo_status = status_map.get(order.status, 'draft')
                
                odoo_values = {
                    'partner_id': customer_mapping.odoo_partner_id,
                    'date_order': order.order_date.strftime('%Y-%m-%d'),
                    'state': odoo_status,
                    'client_order_ref': order.id_code,
                    'company_id': self.integration.company_id,
                    'x_go4rent_id': order.id,
                    'x_go4rent_id_code': order.id_code,
                    'note': order.notes or '',
                }
                
                if mapping:
                    # Update existing order
                    self.client.write('sale.order', [mapping.odoo_sale_order_id], odoo_values)
                    odoo_id = mapping.odoo_sale_order_id
                    
                    # Delete existing order lines
                    order_lines = self.client.search_read(
                        'sale.order.line',
                        domain=[('order_id', '=', odoo_id)],
                        fields=['id']
                    )
                    
                    if order_lines:
                        self.client.unlink('sale.order.line', [line['id'] for line in order_lines])
                else:
                    # Create new order
                    odoo_id = self.client.create('sale.order', odoo_values)
                    mapping = OdooOrderMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_order_id=order.id,
                        odoo_sale_order_id=odoo_id
                    )
                
                # Create order lines
                for item in order_items:
                    # Check if product exists in Odoo
                    product_mapping = OdooProductMapping.objects.filter(
                        odoo_integration=self.integration,
                        go4rent_product_id=item.product.id
                    ).first()
                    
                    if not product_mapping:
                        # Export product first
                        product_sync = OdooSyncService(self.integration_id)
                        product_log = product_sync.sync_products(direction='export')
                        
                        # Try to get mapping again
                        product_mapping = OdooProductMapping.objects.filter(
                            odoo_integration=self.integration,
                            go4rent_product_id=item.product.id
                        ).first()
                        
                        if not product_mapping:
                            raise Exception(f"Product {item.product.id} could not be exported to Odoo")
                    
                    # Get product template variants
                    product_variants = self.client.search_read(
                        'product.product',
                        domain=[('product_tmpl_id', '=', product_mapping.odoo_product_id)],
                        fields=['id']
                    )
                    
                    if not product_variants:
                        raise Exception(f"No product variants found for product template {product_mapping.odoo_product_id}")
                    
                    # Use the first variant
                    product_variant_id = product_variants[0]['id']
                    
                    # Create order line
                    line_values = {
                        'order_id': odoo_id,
                        'product_id': product_variant_id,
                        'name': item.product.name,
                        'product_uom_qty': item.quantity,
                        'price_unit': float(item.price),
                    }
                    
                    self.client.create('sale.order.line', line_values)
                
                details['exported'].append({
                    'go4rent_id': order.id,
                    'go4rent_id_code': order.id_code,
                    'odoo_id': odoo_id,
                    'customer': order.customer.get_full_name(),
                    'status': order.status
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'go4rent_id': order.id,
                    'go4rent_id_code': order.id_code,
                    'customer': order.customer.get_full_name(),
                    'status': order.status,
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error exporting order {order.id_code}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_order_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def _import_orders(self, log):
        """
        Import orders from Odoo to Go4Rent
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get orders from Odoo
        domain = []
        if self.integration.last_order_sync:
            # Convert timezone-aware datetime to string in Odoo format
            last_sync_str = self.integration.last_order_sync.strftime('%Y-%m-%d %H:%M:%S')
            domain.append(('write_date', '>', last_sync_str))
        
        odoo_orders = self.client.search_read(
            'sale.order',
            domain=domain,
            fields=['id', 'name', 'partner_id', 'date_order', 'state', 
                   'client_order_ref', 'note', 'x_go4rent_id']
        )
        
        log.records_processed = len(odoo_orders)
        details = {'imported': [], 'failed': []}
        
        for odoo_order in odoo_orders:
            try:
                # Check if order already exists in Go4Rent
                mapping = None
                
                # Check if order has Go4Rent ID
                if odoo_order.get('x_go4rent_id'):
                    try:
                        order = Order.objects.get(id=odoo_order['x_go4rent_id'])
                        mapping = OdooOrderMapping.objects.filter(
                            odoo_integration=self.integration,
                            go4rent_order_id=order.id
                        ).first()
                    except Order.DoesNotExist:
                        pass
                
                # If no mapping found, check by Odoo ID
                if not mapping:
                    mapping = OdooOrderMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_sale_order_id=odoo_order['id']
                    ).first()
                
                # Get customer mapping
                customer_mapping = OdooCustomerMapping.objects.filter(
                    odoo_integration=self.integration,
                    odoo_partner_id=odoo_order['partner_id'][0]
                ).first()
                
                if not customer_mapping:
                    # Import customer first
                    customer_sync = OdooSyncService(self.integration_id)
                    customer_log = customer_sync.sync_customers(direction='import')
                    
                    # Try to get mapping again
                    customer_mapping = OdooCustomerMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_partner_id=odoo_order['partner_id'][0]
                    ).first()
                    
                    if not customer_mapping:
                        raise Exception(f"Customer {odoo_order['partner_id'][0]} could not be imported from Odoo")
                
                # Map Odoo status to Go4Rent status
                status_map = {
                    'draft': 'pending',
                    'sent': 'confirmed',
                    'sale': 'in_progress',
                    'done': 'completed',
                    'cancel': 'cancelled'
                }
                
                go4rent_status = status_map.get(odoo_order['state'], 'pending')
                
                # Parse date
                import dateutil.parser
                order_date = dateutil.parser.parse(odoo_order['date_order']).date()
                
                if mapping:
                    # Update existing order
                    order = Order.objects.get(id=mapping.go4rent_order_id)
                    order.customer_id = customer_mapping.go4rent_user_id
                    order.order_date = order_date
                    order.status = go4rent_status
                    order.notes = odoo_order.get('note', '')
                    order.save()
                else:
                    # Create new order
                    # Generate a unique ID code
                    id_code = odoo_order.get('client_order_ref')
                    if not id_code:
                        id_code = f"ORD-{Order.objects.count() + 1:03d}"
                    
                    order = Order.objects.create(
                        id_code=id_code,
                        customer_id=customer_mapping.go4rent_user_id,
                        order_date=order_date,
                        status=go4rent_status,
                        payment_status='pending',
                        total_amount=0,  # Will be updated after adding items
                        notes=odoo_order.get('note', '')
                    )
                    
                    mapping = OdooOrderMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_order_id=order.id,
                        odoo_sale_order_id=odoo_order['id']
                    )
                
                # Get order lines
                order_lines = self.client.search_read(
                    'sale.order.line',
                    domain=[('order_id', '=', odoo_order['id'])],
                    fields=['id', 'product_id', 'name', 'product_uom_qty', 'price_unit']
                )
                
                # Delete existing order items
                OrderItem.objects.filter(order=order).delete()
                
                # Create order items
                total_amount = 0
                for line in order_lines:
                    # Get product mapping
                    product_variant_id = line['product_id'][0]
                    
                    # Get product template ID from variant
                    product_variant = self.client.search_read(
                        'product.product',
                        domain=[('id', '=', product_variant_id)],
                        fields=['product_tmpl_id']
                    )
                    
                    if not product_variant:
                        raise Exception(f"Product variant {product_variant_id} not found in Odoo")
                    
                    product_template_id = product_variant[0]['product_tmpl_id'][0]
                    
                    product_mapping = OdooProductMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_product_id=product_template_id
                    ).first()
                    
                    if not product_mapping:
                        # Import product first
                        product_sync = OdooSyncService(self.integration_id)
                        product_log = product_sync.sync_products(direction='import')
                        
                        # Try to get mapping again
                        product_mapping = OdooProductMapping.objects.filter(
                            odoo_integration=self.integration,
                            odoo_product_id=product_template_id
                        ).first()
                        
                        if not product_mapping:
                            raise Exception(f"Product {product_template_id} could not be imported from Odoo")
                    
                    # Create order item
                    quantity = int(line['product_uom_qty'])
                    price = float(line['price_unit'])
                    subtotal = quantity * price
                    
                    OrderItem.objects.create(
                        order=order,
                        product_id=product_mapping.go4rent_product_id,
                        quantity=quantity,
                        price=price,
                        subtotal=subtotal
                    )
                    
                    total_amount += subtotal
                
                # Update order total
                order.total_amount = total_amount
                order.save()
                
                details['imported'].append({
                    'odoo_id': odoo_order['id'],
                    'go4rent_id': order.id,
                    'go4rent_id_code': order.id_code,
                    'customer': order.customer.get_full_name(),
                    'status': order.status
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'odoo_id': odoo_order['id'],
                    'name': odoo_order['name'],
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error importing order {odoo_order['id']}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_order_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def sync_invoices(self, direction='export'):
        """
        Synchronize invoices between Go4Rent and Odoo
        
        Args:
            direction: 'import' or 'export'
            
        Returns:
            OdooSyncLog record
        """
        log = OdooSyncLog.objects.create(
            odoo_integration=self.integration,
            sync_type='invoice',
            direction=direction,
            status='success',
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            details={}
        )
        
        try:
            if direction == 'export':
                return self._export_invoices(log)
            else:
                return self._import_invoices(log)
        except Exception as e:
            log.status = 'error'
            log.error_message = str(e)
            log.save()
            logger.error(f"Error in invoice sync: {str(e)}")
            return log
    
    def _export_invoices(self, log):
        """
        Export invoices from Go4Rent to Odoo
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get invoices to export
        if self.integration.last_invoice_sync:
            invoices = Invoice.objects.filter(
                updated_at__gt=self.integration.last_invoice_sync
            )
        else:
            invoices = Invoice.objects.all()
        
        log.records_processed = invoices.count()
        details = {'exported': [], 'failed': []}
        
        for invoice in invoices:
            try:
                # Check if customer exists in Odoo
                customer_mapping = OdooCustomerMapping.objects.filter(
                    odoo_integration=self.integration,
                    go4rent_user_id=invoice.customer.id
                ).first()
                
                if not customer_mapping:
                    # Export customer first
                    customer_sync = OdooSyncService(self.integration_id)
                    customer_log = customer_sync.sync_customers(direction='export')
                    
                    # Try to get mapping again
                    customer_mapping = OdooCustomerMapping.objects.filter(
                        odoo_integration=self.integration,
                        go4rent_user_id=invoice.customer.id
                    ).first()
                    
                    if not customer_mapping:
                        raise Exception(f"Customer {invoice.customer.id} could not be exported to Odoo")
                
                # Check if invoice already exists in Odoo
                mapping = OdooInvoiceMapping.objects.filter(
                    odoo_integration=self.integration,
                    go4rent_invoice_id=invoice.id
                ).first()
                
                # Get invoice items
                invoice_items = InvoiceItem.objects.filter(invoice=invoice)
                
                # Map status to Odoo status
                status_map = {
                    'draft': 'draft',
                    'sent': 'posted',
                    'paid': 'paid',
                    'partial': 'partial',
                    'overdue': 'posted',
                    'cancelled': 'cancel'
                }
                
                odoo_status = status_map.get(invoice.status, 'draft')
                
                # Check if there's an associated order
                order_mapping = None
                order = Order.objects.filter(id_code=invoice.number.replace('INV-', 'ORD-')).first()
                if order:
                    order_mapping = OdooOrderMapping.objects.filter(
                        odoo_integration=self.integration,
                        go4rent_order_id=order.id
                    ).first()
                
                odoo_values = {
                    'partner_id': customer_mapping.odoo_partner_id,
                    'invoice_date': invoice.issue_date.strftime('%Y-%m-%d'),
                    'invoice_date_due': invoice.due_date.strftime('%Y-%m-%d'),
                    'state': odoo_status,
                    'ref': invoice.id_code,
                    'name': invoice.number,
                    'company_id': self.integration.company_id,
                    'x_go4rent_id': invoice.id,
                    'x_go4rent_id_code': invoice.id_code,
                    'narration': invoice.notes or '',
                }
                
                if order_mapping:
                    odoo_values['invoice_origin'] = order.id_code
                
                if mapping:
                    # Update existing invoice
                    self.client.write('account.move', [mapping.odoo_invoice_id], odoo_values)
                    odoo_id = mapping.odoo_invoice_id
                    
                    # Delete existing invoice lines
                    invoice_lines = self.client.search_read(
                        'account.move.line',
                        domain=[('move_id', '=', odoo_id), ('exclude_from_invoice_tab', '=', False)],
                        fields=['id']
                    )
                    
                    if invoice_lines:
                        self.client.unlink('account.move.line', [line['id'] for line in invoice_lines])
                else:
                    # Create new invoice
                    odoo_values['move_type'] = 'out_invoice'  # Customer invoice
                    odoo_id = self.client.create('account.move', odoo_values)
                    mapping = OdooInvoiceMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_invoice_id=invoice.id,
                        odoo_invoice_id=odoo_id
                    )
                
                # Create invoice lines
                for item in invoice_items:
                    # Create invoice line
                    line_values = {
                        'move_id': odoo_id,
                        'name': item.description,
                        'quantity': item.quantity,
                        'price_unit': float(item.unit_price),
                        'exclude_from_invoice_tab': False,
                    }
                    
                    # Try to find a matching product
                    if 'product' in item.description.lower():
                        product_name = item.description.split(' - ')[0] if ' - ' in item.description else item.description
                        products = Product.objects.filter(name__icontains=product_name)
                        
                        if products.exists():
                            product = products.first()
                            product_mapping = OdooProductMapping.objects.filter(
                                odoo_integration=self.integration,
                                go4rent_product_id=product.id
                            ).first()
                            
                            if product_mapping:
                                # Get product variants
                                product_variants = self.client.search_read(
                                    'product.product',
                                    domain=[('product_tmpl_id', '=', product_mapping.odoo_product_id)],
                                    fields=['id']
                                )
                                
                                if product_variants:
                                    line_values['product_id'] = product_variants[0]['id']
                    
                    self.client.create('account.move.line', line_values)
                
                details['exported'].append({
                    'go4rent_id': invoice.id,
                    'go4rent_id_code': invoice.id_code,
                    'odoo_id': odoo_id,
                    'customer': invoice.customer.get_full_name(),
                    'status': invoice.status
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'go4rent_id': invoice.id,
                    'go4rent_id_code': invoice.id_code,
                    'customer': invoice.customer.get_full_name(),
                    'status': invoice.status,
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error exporting invoice {invoice.id_code}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_invoice_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
    
    def _import_invoices(self, log):
        """
        Import invoices from Odoo to Go4Rent
        
        Args:
            log: OdooSyncLog record
            
        Returns:
            Updated OdooSyncLog record
        """
        # Get invoices from Odoo
        domain = [('move_type', '=', 'out_invoice')]  # Customer invoices only
        if self.integration.last_invoice_sync:
            # Convert timezone-aware datetime to string in Odoo format
            last_sync_str = self.integration.last_invoice_sync.strftime('%Y-%m-%d %H:%M:%S')
            domain.append(('write_date', '>', last_sync_str))
        
        odoo_invoices = self.client.search_read(
            'account.move',
            domain=domain,
            fields=['id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due', 
                   'state', 'ref', 'narration', 'amount_total', 'amount_residual',
                   'invoice_origin', 'x_go4rent_id']
        )
        
        log.records_processed = len(odoo_invoices)
        details = {'imported': [], 'failed': []}
        
        for odoo_invoice in odoo_invoices:
            try:
                # Check if invoice already exists in Go4Rent
                mapping = None
                
                # Check if invoice has Go4Rent ID
                if odoo_invoice.get('x_go4rent_id'):
                    try:
                        invoice = Invoice.objects.get(id=odoo_invoice['x_go4rent_id'])
                        mapping = OdooInvoiceMapping.objects.filter(
                            odoo_integration=self.integration,
                            go4rent_invoice_id=invoice.id
                        ).first()
                    except Invoice.DoesNotExist:
                        pass
                
                # If no mapping found, check by Odoo ID
                if not mapping:
                    mapping = OdooInvoiceMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_invoice_id=odoo_invoice['id']
                    ).first()
                
                # Get customer mapping
                customer_mapping = OdooCustomerMapping.objects.filter(
                    odoo_integration=self.integration,
                    odoo_partner_id=odoo_invoice['partner_id'][0]
                ).first()
                
                if not customer_mapping:
                    # Import customer first
                    customer_sync = OdooSyncService(self.integration_id)
                    customer_log = customer_sync.sync_customers(direction='import')
                    
                    # Try to get mapping again
                    customer_mapping = OdooCustomerMapping.objects.filter(
                        odoo_integration=self.integration,
                        odoo_partner_id=odoo_invoice['partner_id'][0]
                    ).first()
                    
                    if not customer_mapping:
                        raise Exception(f"Customer {odoo_invoice['partner_id'][0]} could not be imported from Odoo")
                
                # Map Odoo status to Go4Rent status
                status_map = {
                    'draft': 'draft',
                    'posted': 'sent',
                    'paid': 'paid',
                    'partial': 'partial',
                    'cancel': 'cancelled'
                }
                
                go4rent_status = status_map.get(odoo_invoice['state'], 'draft')
                
                # Parse dates
                import dateutil.parser
                issue_date = dateutil.parser.parse(odoo_invoice['invoice_date']).date() if odoo_invoice.get('invoice_date') else timezone.now().date()
                due_date = dateutil.parser.parse(odoo_invoice['invoice_date_due']).date() if odoo_invoice.get('invoice_date_due') else (issue_date + timedelta(days=30))
                
                # Calculate paid amount
                amount_total = float(odoo_invoice['amount_total'])
                amount_residual = float(odoo_invoice['amount_residual'])
                paid_amount = amount_total - amount_residual
                
                if mapping:
                    # Update existing invoice
                    invoice = Invoice.objects.get(id=mapping.go4rent_invoice_id)
                    invoice.customer_id = customer_mapping.go4rent_user_id
                    invoice.issue_date = issue_date
                    invoice.due_date = due_date
                    invoice.status = go4rent_status
                    invoice.amount = amount_total
                    invoice.paid_amount = paid_amount
                    invoice.notes = odoo_invoice.get('narration', '')
                    invoice.save()
                else:
                    # Create new invoice
                    # Generate a unique ID code and number
                    id_code = odoo_invoice.get('ref')
                    if not id_code:
                        id_code = f"INV-{Invoice.objects.count() + 1:03d}"
                    
                    number = odoo_invoice.get('name')
                    if not number or number == '/':
                        number = f"INV-{Invoice.objects.count() + 1:06d}"
                    
                    invoice = Invoice.objects.create(
                        id_code=id_code,
                        number=number,
                        customer_id=customer_mapping.go4rent_user_id,
                        issue_date=issue_date,
                        due_date=due_date,
                        status=go4rent_status,
                        amount=amount_total,
                        paid_amount=paid_amount,
                        notes=odoo_invoice.get('narration', '')
                    )
                    
                    mapping = OdooInvoiceMapping.objects.create(
                        odoo_integration=self.integration,
                        go4rent_invoice_id=invoice.id,
                        odoo_invoice_id=odoo_invoice['id']
                    )
                
                # Get invoice lines
                invoice_lines = self.client.search_read(
                    'account.move.line',
                    domain=[('move_id', '=', odoo_invoice['id']), ('exclude_from_invoice_tab', '=', False)],
                    fields=['id', 'name', 'quantity', 'price_unit', 'price_subtotal']
                )
                
                # Delete existing invoice items
                InvoiceItem.objects.filter(invoice=invoice).delete()
                
                # Create invoice items
                for line in invoice_lines:
                    # Create invoice item
                    quantity = int(line['quantity'])
                    unit_price = float(line['price_unit'])
                    amount = float(line['price_subtotal'])
                    
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=line['name'],
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount
                    )
                
                details['imported'].append({
                    'odoo_id': odoo_invoice['id'],
                    'go4rent_id': invoice.id,
                    'go4rent_id_code': invoice.id_code,
                    'customer': invoice.customer.get_full_name(),
                    'status': invoice.status
                })
                
                log.records_succeeded += 1
                
            except Exception as e:
                details['failed'].append({
                    'odoo_id': odoo_invoice['id'],
                    'name': odoo_invoice.get('name', f"Invoice {odoo_invoice['id']}"),
                    'error': str(e)
                })
                
                log.records_failed += 1
                logger.error(f"Error importing invoice {odoo_invoice['id']}: {str(e)}")
        
        # Update last sync timestamp
        self.integration.last_invoice_sync = timezone.now()
        self.integration.save()
        
        log.details = details
        log.save()
        
        return log
