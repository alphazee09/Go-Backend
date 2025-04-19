# Backend Documentation for Go4Rent Dashboard

## Overview

This document provides comprehensive documentation for the Go4Rent Dashboard backend implementation. The backend is built using Django and PostgreSQL, providing a robust API for the frontend to interact with.

## Technology Stack

- **Framework**: Django 5.2
- **Database**: PostgreSQL
- **API**: Django REST Framework
- **Authentication**: Token-based authentication
- **Dependencies**:
  - django-cors-headers
  - django-filter
  - djangorestframework
  - psycopg2-binary
  - Pillow

## Project Structure

```
go4rent_backend/
├── go4rent/                  # Main Django project settings
│   ├── settings.py           # Project settings
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI configuration
├── api/                      # Main application
│   ├── management/           # Custom management commands
│   │   └── commands/         
│   │       └── seed_data.py  # Data seeding command
│   ├── migrations/           # Database migrations
│   ├── models.py             # Database models
│   ├── serializers.py        # API serializers
│   ├── views.py              # API views and viewsets
│   ├── urls.py               # API URL routing
│   ├── dashboard.py          # Dashboard API endpoints
│   ├── dashboard_urls.py     # Dashboard URL routing
│   ├── signals.py            # Business logic signals
│   └── admin.py              # Admin interface configuration
├── venv/                     # Virtual environment
└── manage.py                 # Django management script
```

## Database Schema

The database schema is designed to support all the functionality required by the Go4Rent dashboard, including user management, inventory management, order processing, financial operations, reporting, and system settings.

### Core Models

#### User Management

- **User**: Custom user model extending Django's AbstractUser
  - Fields: username, email, first_name, last_name, phone, address, role, status, avatar, last_active, loyalty_points
  - Relationships: orders, transactions, invoices, documents, payment_methods

- **UserDocument**: Documents uploaded by users
  - Fields: user, name, file, upload_date, verified

- **PaymentMethod**: User payment methods
  - Fields: user, type, last4, expiry, default

#### Inventory Management

- **Category**: Product categories
  - Fields: name, description

- **Warehouse**: Storage locations
  - Fields: name, location, address

- **Product**: Rental items
  - Fields: id_code, name, sku, category, description, image, rental_price, replacement_value, stock, min_stock_level, max_stock_level, available_for_rent, currently_rented, under_maintenance, status
  - Relationships: specifications, included_items, locations, maintenance_records

- **ProductSpecification**: Technical specifications
  - Fields: product, name, value

- **ProductIncludedItem**: Items included with product
  - Fields: product, name

- **ProductLocation**: Where products are stored
  - Fields: product, warehouse, section, shelf, bin, quantity

- **MaintenanceRecord**: Maintenance history
  - Fields: product, date, type, description, status, technician, cost, notes

#### Order Management

- **Order**: Rental orders
  - Fields: id_code, customer, order_date, status, payment_status, total_amount, notes
  - Relationships: items, timeline, delivery_address, rental_period

- **OrderItem**: Individual items in an order
  - Fields: order, product, quantity, price, subtotal

- **DeliveryAddress**: Shipping information
  - Fields: order, address_line1, address_line2, city, state, postal_code, country

- **RentalPeriod**: Rental duration
  - Fields: order, start_date, end_date, extended

- **OrderTimeline**: Order status history
  - Fields: order, type, date, description, user

#### Financial Management

- **Transaction**: Financial transactions
  - Fields: id_code, customer, type, amount, status, date, time, payment_method, reference, notes
  - Relationships: timeline, invoice

- **TransactionTimeline**: Transaction history
  - Fields: transaction, title, timestamp, description

- **Invoice**: Billing documents
  - Fields: id_code, number, customer, amount, paid_amount, status, issue_date, due_date, notes
  - Relationships: items, billing_address

- **InvoiceItem**: Individual items in an invoice
  - Fields: invoice, description, quantity, unit_price, amount

- **BillingAddress**: Invoice address
  - Fields: invoice, address_line1, address_line2, city, state, postal_code, country

#### Reporting

- **Report**: Generated reports
  - Fields: id_code, name, type, date, file, status, created_by, notes

#### System Settings

- **CompanySettings**: Global settings
  - Fields: company_name, website, email, phone, address, timezone, date_format, currency

- **Role**: User roles
  - Fields: name, description
  - Relationships: permissions

- **RolePermission**: Role-based permissions
  - Fields: role, permission

- **NotificationSetting**: Notification preferences
  - Fields: category, email, in_app, sms

- **Integration**: External system integrations
  - Fields: name, type, api_key, status, last_sync, description
  - Relationships: tags

- **IntegrationTag**: Integration metadata
  - Fields: integration, key, value

## API Endpoints

The backend provides a comprehensive REST API for the frontend to interact with. All endpoints are prefixed with `/api/`.

### Authentication

- `POST /api/auth/token/`: Obtain authentication token

### User Management

- `GET /api/users/`: List all users
- `POST /api/users/`: Create a new user
- `GET /api/users/{id}/`: Retrieve a specific user
- `PUT /api/users/{id}/`: Update a user
- `DELETE /api/users/{id}/`: Delete a user
- `GET /api/user-documents/`: List user documents
- `GET /api/payment-methods/`: List payment methods

### Inventory Management

- `GET /api/categories/`: List all categories
- `GET /api/warehouses/`: List all warehouses
- `GET /api/products/`: List all products
- `POST /api/products/`: Create a new product
- `GET /api/products/{id}/`: Retrieve a specific product
- `PUT /api/products/{id}/`: Update a product
- `DELETE /api/products/{id}/`: Delete a product
- `GET /api/product-specifications/`: List product specifications
- `GET /api/product-included-items/`: List included items
- `GET /api/product-locations/`: List product locations
- `GET /api/maintenance-records/`: List maintenance records

### Order Management

- `GET /api/orders/`: List all orders
- `POST /api/orders/`: Create a new order
- `GET /api/orders/{id}/`: Retrieve a specific order
- `PUT /api/orders/{id}/`: Update an order
- `DELETE /api/orders/{id}/`: Delete an order
- `GET /api/order-items/`: List order items
- `GET /api/delivery-addresses/`: List delivery addresses
- `GET /api/rental-periods/`: List rental periods
- `GET /api/order-timeline/`: List order timeline events

### Financial Management

- `GET /api/transactions/`: List all transactions
- `POST /api/transactions/`: Create a new transaction
- `GET /api/transactions/{id}/`: Retrieve a specific transaction
- `PUT /api/transactions/{id}/`: Update a transaction
- `GET /api/transaction-timeline/`: List transaction timeline events
- `GET /api/invoices/`: List all invoices
- `POST /api/invoices/`: Create a new invoice
- `GET /api/invoices/{id}/`: Retrieve a specific invoice
- `PUT /api/invoices/{id}/`: Update an invoice
- `GET /api/invoice-items/`: List invoice items
- `GET /api/billing-addresses/`: List billing addresses

### Reporting

- `GET /api/reports/`: List all reports
- `POST /api/reports/`: Create a new report
- `GET /api/reports/{id}/`: Retrieve a specific report
- `PUT /api/reports/{id}/`: Update a report
- `DELETE /api/reports/{id}/`: Delete a report

### System Settings

- `GET /api/company-settings/`: List company settings
- `GET /api/roles/`: List all roles
- `GET /api/role-permissions/`: List role permissions
- `GET /api/notification-settings/`: List notification settings
- `GET /api/integrations/`: List all integrations
- `GET /api/integration-tags/`: List integration tags

### Dashboard

- `GET /api/dashboard/stats/`: Get dashboard statistics
- `GET /api/dashboard/inventory/`: Get inventory statistics
- `GET /api/dashboard/financial/`: Get financial statistics
- `GET /api/dashboard/customers/`: Get customer statistics
- `POST /api/dashboard/generate-report/`: Generate a new report
- `GET /api/search/`: Global search across multiple models

## Business Logic

The backend implements business logic through Django signals to handle various events in the system:

1. **User Creation**: Automatically creates an authentication token for new users
2. **Order Status Changes**: Updates product stock levels when order status changes
3. **Order Timeline**: Creates timeline events when order status changes
4. **Maintenance Records**: Updates product maintenance status
5. **Transaction Timeline**: Creates timeline events for transactions
6. **Invoice Status**: Updates invoice status when payment is received

## Authentication and Permissions

The backend uses token-based authentication with Django REST Framework's TokenAuthentication. Permissions are role-based, with different roles having access to different parts of the system:

- **Admin**: Full access to all system features and settings
- **Manager**: Manage day-to-day operations and staff
- **Staff**: Handle customer orders and inventory
- **Customer**: Access to customer portal and order history

## Data Seeding

The backend includes a data seeding command to populate the database with initial data:

```bash
python manage.py seed_data
```

This command creates:
- Admin user
- User roles with permissions
- Company settings
- Notification settings
- Product categories
- Warehouses
- Sample products with specifications, included items, and locations

## Production Deployment

For production deployment, the following steps are recommended:

1. Update `settings.py` with production settings:
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Set up a proper `SECRET_KEY`
   - Configure email settings

2. Set up a production database:
   - Create a dedicated PostgreSQL database
   - Update database settings in `settings.py`

3. Set up static files:
   - Run `python manage.py collectstatic`
   - Configure a web server to serve static files

4. Set up a WSGI server (e.g., Gunicorn):
   ```bash
   gunicorn go4rent.wsgi:application
   ```

5. Set up a reverse proxy (e.g., Nginx) to handle requests

6. Configure SSL/TLS for secure connections

7. Set up database backups

8. Configure monitoring and logging

## Conclusion

This backend implementation provides a complete solution for the Go4Rent dashboard, with all the necessary functionality to support the frontend. The API is designed to be flexible and extensible, allowing for future enhancements and additions.
