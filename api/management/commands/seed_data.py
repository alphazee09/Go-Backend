from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import (
    Category, Warehouse, Product, ProductSpecification, ProductIncludedItem, ProductLocation,
    Role, RolePermission, CompanySettings, NotificationSetting
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed initial data for the Go4Rent application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial data...')
        
        # Create admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@go4rent.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
            )
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.role = 'admin'
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        
        # Create roles
        self.create_roles()
        
        # Create company settings
        self.create_company_settings()
        
        # Create notification settings
        self.create_notification_settings()
        
        # Create product categories
        self.create_categories()
        
        # Create warehouses
        self.create_warehouses()
        
        # Create sample products
        self.create_sample_products()
        
        self.stdout.write(self.style.SUCCESS('Initial data seeding completed'))
    
    def create_roles(self):
        roles = [
            {
                'name': 'Administrator',
                'description': 'Full access to all system features and settings',
                'permissions': [
                    'users.view', 'users.manage',
                    'inventory.view', 'inventory.manage',
                    'orders.view', 'orders.manage',
                    'finance.view', 'finance.manage',
                    'tracking.view', 'tracking.manage',
                    'reports.view', 'reports.manage',
                    'settings.view', 'settings.manage'
                ]
            },
            {
                'name': 'Manager',
                'description': 'Manage day-to-day operations and staff',
                'permissions': [
                    'users.view',
                    'inventory.view', 'inventory.manage',
                    'orders.view', 'orders.manage',
                    'finance.view', 'finance.manage',
                    'tracking.view', 'tracking.manage',
                    'reports.view', 'reports.manage',
                    'settings.view'
                ]
            },
            {
                'name': 'Staff',
                'description': 'Handle customer orders and inventory',
                'permissions': [
                    'users.view',
                    'inventory.view',
                    'orders.view', 'orders.manage',
                    'finance.view',
                    'tracking.view',
                    'reports.view'
                ]
            },
            {
                'name': 'Customer',
                'description': 'Access to customer portal and order history',
                'permissions': [
                    'orders.view',
                    'inventory.view'
                ]
            }
        ]
        
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            
            if created:
                self.stdout.write(f'Created role: {role.name}')
                
                # Add permissions
                for permission in role_data['permissions']:
                    RolePermission.objects.create(
                        role=role,
                        permission=permission
                    )
    
    def create_company_settings(self):
        if not CompanySettings.objects.exists():
            CompanySettings.objects.create(
                company_name='Go4Rent Equipment Rentals',
                website='https://go4rent.example.com',
                email='info@go4rent.example.com',
                phone='(123) 456-7890',
                address='123 Main Street, San Francisco, CA 94105',
                timezone='America/Los_Angeles',
                date_format='MM/DD/YYYY',
                currency='USD'
            )
            self.stdout.write(self.style.SUCCESS('Company settings created'))
    
    def create_notification_settings(self):
        categories = ['orders', 'inventory', 'system', 'marketing']
        
        for category in categories:
            NotificationSetting.objects.get_or_create(
                category=category,
                defaults={
                    'email': True,
                    'in_app': True,
                    'sms': category == 'system'  # SMS only for system notifications by default
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Notification settings created'))
    
    def create_categories(self):
        categories = [
            'Cameras', 'Drones', 'Audio', 'Lighting', 'Computers',
            'Projectors', 'Screens', 'Tripods', 'Lenses', 'Accessories'
        ]
        
        for category_name in categories:
            Category.objects.get_or_create(name=category_name)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} product categories'))
    
    def create_warehouses(self):
        warehouses = [
            {
                'name': 'Main Warehouse',
                'location': 'San Francisco',
                'address': '123 Main Street, San Francisco, CA 94105'
            },
            {
                'name': 'East Coast Warehouse',
                'location': 'New York',
                'address': '456 Broadway, New York, NY 10013'
            },
            {
                'name': 'Midwest Warehouse',
                'location': 'Chicago',
                'address': '789 Michigan Ave, Chicago, IL 60611'
            }
        ]
        
        for warehouse_data in warehouses:
            Warehouse.objects.get_or_create(
                name=warehouse_data['name'],
                defaults={
                    'location': warehouse_data['location'],
                    'address': warehouse_data['address']
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(warehouses)} warehouses'))
    
    def create_sample_products(self):
        # Only create sample products if none exist
        if Product.objects.exists():
            self.stdout.write('Products already exist, skipping sample product creation')
            return
        
        # Get categories
        camera_category = Category.objects.get(name='Cameras')
        drone_category = Category.objects.get(name='Drones')
        audio_category = Category.objects.get(name='Audio')
        lighting_category = Category.objects.get(name='Lighting')
        
        # Get warehouses
        main_warehouse = Warehouse.objects.get(name='Main Warehouse')
        
        # Create sample products
        products = [
            {
                'id_code': 'PRD-001',
                'name': 'Sony Alpha A7 III',
                'sku': 'CAM-SONY-A7III',
                'category': camera_category,
                'description': 'Full-frame mirrorless camera with excellent low-light performance and 4K video recording capabilities.',
                'rental_price': 85.0,
                'replacement_value': 1999.99,
                'stock': 5,
                'min_stock_level': 2,
                'max_stock_level': 10,
                'available_for_rent': 5,
                'currently_rented': 0,
                'under_maintenance': 0,
                'status': 'active',
                'specifications': [
                    {'name': 'Sensor', 'value': '24.2MP Full-Frame Exmor R BSI CMOS'},
                    {'name': 'ISO Range', 'value': '100-51200 (Expandable to 50-204800)'},
                    {'name': 'Video Resolution', 'value': '4K UHD 2160p'},
                    {'name': 'Weight', 'value': '650g (1.43 lb)'},
                    {'name': 'Battery Life', 'value': 'Approx. 710 shots'},
                ],
                'included_items': [
                    'Camera Body',
                    '24-70mm f/2.8 Lens',
                    'Battery (2x)',
                    'Battery Charger',
                    'Neck Strap',
                    'USB Cable',
                    'Camera Bag',
                ],
                'location': {
                    'warehouse': main_warehouse,
                    'section': 'A',
                    'shelf': '3',
                    'bin': 'B12',
                }
            },
            {
                'id_code': 'PRD-002',
                'name': 'DJI Mavic 3 Pro',
                'sku': 'DRN-DJI-MAV3P',
                'category': drone_category,
                'description': 'Professional drone with Hasselblad camera, 4/3 CMOS sensor, and up to 46 minutes of flight time.',
                'rental_price': 120.0,
                'replacement_value': 2499.99,
                'stock': 3,
                'min_stock_level': 1,
                'max_stock_level': 5,
                'available_for_rent': 3,
                'currently_rented': 0,
                'under_maintenance': 0,
                'status': 'active',
                'specifications': [
                    {'name': 'Camera', 'value': 'Hasselblad L2D-20c'},
                    {'name': 'Sensor', 'value': '4/3 CMOS'},
                    {'name': 'Max Flight Time', 'value': '46 minutes'},
                    {'name': 'Max Speed', 'value': '47 mph (75 kph)'},
                    {'name': 'Weight', 'value': '895g (1.97 lb)'},
                ],
                'included_items': [
                    'Drone',
                    'Remote Controller',
                    '3x Batteries',
                    'Battery Charging Hub',
                    'Propellers (3 pairs)',
                    'Storage Case',
                    'ND Filters Set',
                ],
                'location': {
                    'warehouse': main_warehouse,
                    'section': 'B',
                    'shelf': '1',
                    'bin': 'D05',
                }
            },
            {
                'id_code': 'PRD-003',
                'name': 'Sennheiser MKH 416',
                'sku': 'AUD-SEN-MKH416',
                'category': audio_category,
                'description': 'Professional short shotgun interference tube microphone for film, TV, and outdoor recording.',
                'rental_price': 45.0,
                'replacement_value': 999.99,
                'stock': 8,
                'min_stock_level': 3,
                'max_stock_level': 12,
                'available_for_rent': 8,
                'currently_rented': 0,
                'under_maintenance': 0,
                'status': 'active',
                'specifications': [
                    {'name': 'Type', 'value': 'Shotgun Microphone'},
                    {'name': 'Frequency Response', 'value': '40 Hz to 20 kHz'},
                    {'name': 'Sensitivity', 'value': '25 mV/Pa'},
                    {'name': 'Max SPL', 'value': '130 dB'},
                    {'name': 'Weight', 'value': '175g (0.39 lb)'},
                ],
                'included_items': [
                    'Microphone',
                    'Windshield',
                    'Shockmount',
                    'XLR Cable',
                    'Carrying Case',
                ],
                'location': {
                    'warehouse': main_warehouse,
                    'section': 'C',
                    'shelf': '2',
                    'bin': 'A08',
                }
            },
            {
                'id_code': 'PRD-004',
                'name': 'Aputure 300d Mark II',
                'sku': 'LGT-APT-300D2',
                'category': lighting_category,
                'description': 'Professional LED light with 300W output, color temperature of 5500K, and various lighting effects.',
                'rental_price': 65.0,
                'replacement_value': 1099.99,
                'stock': 6,
                'min_stock_level': 2,
                'max_stock_level': 8,
                'available_for_rent': 6,
                'currently_rented': 0,
                'under_maintenance': 0,
                'status': 'active',
                'specifications': [
                    {'name': 'Power', 'value': '300W'},
                    {'name': 'Color Temperature', 'value': '5500K'},
                    {'name': 'CRI/TLCI', 'value': '≥96'},
                    {'name': 'Beam Angle', 'value': '55°'},
                    {'name': 'Weight', 'value': '3.1kg (6.8 lb)'},
                ],
                'included_items': [
                    'Light Head',
                    'Controller Box',
                    'Power Supply',
                    'Reflector',
                    'Carrying Case',
                    'Barn Doors',
                ],
                'location': {
                    'warehouse': main_warehouse,
                    'section': 'D',
                    'shelf': '4',
                    'bin': 'C15',
                }
            },
        ]
        
        for product_data in products:
            # Create the product
            product = Product.objects.create(
                id_code=product_data['id_code'],
                name=product_data['name'],
                sku=product_data['sku'],
                category=product_data['category'],
                description=product_data['description'],
                rental_price=product_data['rental_price'],
                replacement_value=product_data['replacement_value'],
                stock=product_data['stock'],
                min_stock_level=product_data['min_stock_level'],
                max_stock_level=product_data['max_stock_level'],
                available_for_rent=product_data['available_for_rent'],
                currently_rented=product_data['currently_rented'],
                under_maintenance=product_data['under_maintenance'],
                status=product_data['status']
            )
            
            # Add specifications
            for spec in product_data['specifications']:
                ProductSpecification.objects.create(
                    product=product,
                    name=spec['name'],
                    value=spec['value']
                )
            
            # Add included items
            for item in product_data['included_items']:
                ProductIncludedItem.objects.create(
                    product=product,
                    name=item
                )
            
            # Add location
            location_data = product_data['location']
            ProductLocation.objects.create(
                product=product,
                warehouse=location_data['warehouse'],
                section=location_data['section'],
                shelf=location_data['shelf'],
                bin=location_data['bin'],
                quantity=product.stock
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(products)} sample products'))
