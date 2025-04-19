# Go4Rent Dashboard Database Schema

This document provides a detailed description of the database schema for the Go4Rent Dashboard application.

## Entity Relationship Diagram

```
+----------------+       +----------------+       +----------------+
|      User      |       |     Product    |       |     Order      |
+----------------+       +----------------+       +----------------+
| id             |       | id             |       | id             |
| username       |       | id_code        |       | id_code        |
| email          |       | name           |       | customer_id    |
| password       |       | sku            |       | order_date     |
| first_name     |       | category_id    |       | status         |
| last_name      |       | description    |       | payment_status |
| phone          |       | image          |       | total_amount   |
| address        |       | rental_price   |       | notes          |
| role           |       | replacement_val|       | created_at     |
| status         |       | stock          |       | updated_at     |
| avatar         |       | min_stock_level|       +----------------+
| last_active    |       | max_stock_level|             |
| loyalty_points |       | available_rent |             |
| is_staff       |       | currently_rent |             |
| is_superuser   |       | under_maint    |             |
| is_active      |       | status         |             |
| date_joined    |       | created_at     |             |
| last_login     |       | updated_at     |             |
+----------------+       +----------------+             |
       |                        |                       |
       |                        |                       |
       v                        v                       v
+----------------+       +----------------+       +----------------+
| UserDocument   |       | ProductSpec    |       |   OrderItem    |
+----------------+       +----------------+       +----------------+
| id             |       | id             |       | id             |
| user_id        |       | product_id     |       | order_id       |
| name           |       | name           |       | product_id     |
| file           |       | value          |       | quantity       |
| upload_date    |       +----------------+       | price          |
| verified       |                                | subtotal       |
+----------------+                                +----------------+
       |                        |                       |
       |                        |                       |
       v                        v                       v
+----------------+       +----------------+       +----------------+
| PaymentMethod  |       | ProductIncluded|       |DeliveryAddress |
+----------------+       +----------------+       +----------------+
| id             |       | id             |       | id             |
| user_id        |       | product_id     |       | order_id       |
| type           |       | name           |       | address_line1  |
| last4          |       +----------------+       | address_line2  |
| expiry         |                                | city           |
| default_method |                                | state          |
+----------------+                                | postal_code    |
                                                  | country        |
                                                  +----------------+
```

## Tables

### User Management

#### users
- **id**: Serial, Primary Key
- **username**: VARCHAR(150), Not Null, Unique
- **email**: VARCHAR(254), Not Null, Unique
- **password**: VARCHAR(128), Not Null
- **first_name**: VARCHAR(150)
- **last_name**: VARCHAR(150)
- **phone**: VARCHAR(20)
- **address**: TEXT
- **role**: VARCHAR(20), Not Null
- **status**: VARCHAR(20), Not Null, Default 'active'
- **avatar**: VARCHAR(255)
- **last_active**: TIMESTAMP
- **loyalty_points**: INTEGER, Default 0
- **is_staff**: BOOLEAN, Default FALSE
- **is_superuser**: BOOLEAN, Default FALSE
- **is_active**: BOOLEAN, Default TRUE
- **date_joined**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **last_login**: TIMESTAMP

#### user_documents
- **id**: Serial, Primary Key
- **user_id**: INTEGER, Foreign Key to users(id)
- **name**: VARCHAR(255), Not Null
- **file**: VARCHAR(255), Not Null
- **upload_date**: DATE, Not Null, Default CURRENT_DATE
- **verified**: BOOLEAN, Default FALSE

#### payment_methods
- **id**: Serial, Primary Key
- **user_id**: INTEGER, Foreign Key to users(id)
- **type**: VARCHAR(50), Not Null
- **last4**: VARCHAR(4), Not Null
- **expiry**: VARCHAR(7), Not Null
- **default_method**: BOOLEAN, Default FALSE

### Inventory Management

#### categories
- **id**: Serial, Primary Key
- **name**: VARCHAR(100), Not Null, Unique
- **description**: TEXT

#### warehouses
- **id**: Serial, Primary Key
- **name**: VARCHAR(100), Not Null
- **location**: VARCHAR(100), Not Null
- **address**: TEXT

#### products
- **id**: Serial, Primary Key
- **id_code**: VARCHAR(20), Not Null, Unique
- **name**: VARCHAR(255), Not Null
- **sku**: VARCHAR(50), Not Null, Unique
- **category_id**: INTEGER, Foreign Key to categories(id)
- **description**: TEXT
- **image**: VARCHAR(255)
- **rental_price**: DECIMAL(10, 2), Not Null
- **replacement_value**: DECIMAL(10, 2), Not Null
- **stock**: INTEGER, Not Null, Default 0
- **min_stock_level**: INTEGER, Default 0
- **max_stock_level**: INTEGER, Default 0
- **available_for_rent**: INTEGER, Not Null, Default 0
- **currently_rented**: INTEGER, Not Null, Default 0
- **under_maintenance**: INTEGER, Not Null, Default 0
- **status**: VARCHAR(20), Not Null, Default 'active'
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

#### product_specifications
- **id**: Serial, Primary Key
- **product_id**: INTEGER, Foreign Key to products(id)
- **name**: VARCHAR(100), Not Null
- **value**: TEXT, Not Null

#### product_included_items
- **id**: Serial, Primary Key
- **product_id**: INTEGER, Foreign Key to products(id)
- **name**: VARCHAR(255), Not Null

#### product_locations
- **id**: Serial, Primary Key
- **product_id**: INTEGER, Foreign Key to products(id)
- **warehouse_id**: INTEGER, Foreign Key to warehouses(id)
- **section**: VARCHAR(20), Not Null
- **shelf**: VARCHAR(20), Not Null
- **bin**: VARCHAR(20), Not Null
- **quantity**: INTEGER, Not Null, Default 0

#### maintenance_records
- **id**: Serial, Primary Key
- **product_id**: INTEGER, Foreign Key to products(id)
- **date**: DATE, Not Null, Default CURRENT_DATE
- **type**: VARCHAR(50), Not Null
- **description**: TEXT, Not Null
- **status**: VARCHAR(20), Not Null, Default 'scheduled'
- **technician**: VARCHAR(100)
- **cost**: DECIMAL(10, 2), Default 0
- **notes**: TEXT

### Order Management

#### orders
- **id**: Serial, Primary Key
- **id_code**: VARCHAR(20), Not Null, Unique
- **customer_id**: INTEGER, Foreign Key to users(id)
- **order_date**: DATE, Not Null, Default CURRENT_DATE
- **status**: VARCHAR(20), Not Null, Default 'pending'
- **payment_status**: VARCHAR(20), Not Null, Default 'pending'
- **total_amount**: DECIMAL(10, 2), Not Null, Default 0
- **notes**: TEXT
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

#### order_items
- **id**: Serial, Primary Key
- **order_id**: INTEGER, Foreign Key to orders(id)
- **product_id**: INTEGER, Foreign Key to products(id)
- **quantity**: INTEGER, Not Null, Default 1
- **price**: DECIMAL(10, 2), Not Null
- **subtotal**: DECIMAL(10, 2), Not Null

#### delivery_addresses
- **id**: Serial, Primary Key
- **order_id**: INTEGER, Foreign Key to orders(id)
- **address_line1**: VARCHAR(255), Not Null
- **address_line2**: VARCHAR(255)
- **city**: VARCHAR(100), Not Null
- **state**: VARCHAR(100), Not Null
- **postal_code**: VARCHAR(20), Not Null
- **country**: VARCHAR(100), Not Null, Default 'United States'

#### rental_periods
- **id**: Serial, Primary Key
- **order_id**: INTEGER, Foreign Key to orders(id)
- **start_date**: DATE, Not Null
- **end_date**: DATE, Not Null
- **extended**: BOOLEAN, Default FALSE

#### order_timeline
- **id**: Serial, Primary Key
- **order_id**: INTEGER, Foreign Key to orders(id)
- **type**: VARCHAR(50), Not Null
- **date**: TIMESTAMP, Not Null, Default CURRENT_TIMESTAMP
- **description**: TEXT, Not Null
- **user**: VARCHAR(100), Not Null

### Financial Management

#### transactions
- **id**: Serial, Primary Key
- **id_code**: VARCHAR(20), Not Null, Unique
- **customer_id**: INTEGER, Foreign Key to users(id)
- **invoice_id**: INTEGER, Foreign Key to invoices(id)
- **type**: VARCHAR(20), Not Null
- **amount**: DECIMAL(10, 2), Not Null
- **status**: VARCHAR(20), Not Null, Default 'pending'
- **date**: DATE, Not Null, Default CURRENT_DATE
- **time**: TIME, Not Null, Default CURRENT_TIME
- **payment_method**: VARCHAR(50)
- **reference**: VARCHAR(100)
- **notes**: TEXT
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

#### transaction_timeline
- **id**: Serial, Primary Key
- **transaction_id**: INTEGER, Foreign Key to transactions(id)
- **title**: VARCHAR(100), Not Null
- **timestamp**: TIMESTAMP, Not Null, Default CURRENT_TIMESTAMP
- **description**: TEXT, Not Null

#### invoices
- **id**: Serial, Primary Key
- **id_code**: VARCHAR(20), Not Null, Unique
- **number**: VARCHAR(50), Not Null, Unique
- **customer_id**: INTEGER, Foreign Key to users(id)
- **amount**: DECIMAL(10, 2), Not Null, Default 0
- **paid_amount**: DECIMAL(10, 2), Not Null, Default 0
- **status**: VARCHAR(20), Not Null, Default 'draft'
- **issue_date**: DATE, Not Null, Default CURRENT_DATE
- **due_date**: DATE, Not Null
- **notes**: TEXT
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

#### invoice_items
- **id**: Serial, Primary Key
- **invoice_id**: INTEGER, Foreign Key to invoices(id)
- **description**: TEXT, Not Null
- **quantity**: INTEGER, Not Null, Default 1
- **unit_price**: DECIMAL(10, 2), Not Null
- **amount**: DECIMAL(10, 2), Not Null

#### billing_addresses
- **id**: Serial, Primary Key
- **invoice_id**: INTEGER, Foreign Key to invoices(id)
- **address_line1**: VARCHAR(255), Not Null
- **address_line2**: VARCHAR(255)
- **city**: VARCHAR(100), Not Null
- **state**: VARCHAR(100), Not Null
- **postal_code**: VARCHAR(20), Not Null
- **country**: VARCHAR(100), Not Null, Default 'United States'

### Reporting

#### reports
- **id**: Serial, Primary Key
- **id_code**: VARCHAR(20), Not Null, Unique
- **name**: VARCHAR(255), Not Null
- **type**: VARCHAR(50), Not Null
- **date**: DATE, Not Null, Default CURRENT_DATE
- **file**: VARCHAR(255)
- **status**: VARCHAR(20), Not Null, Default 'processing'
- **created_by_id**: INTEGER, Foreign Key to users(id)
- **notes**: TEXT
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

### System Settings

#### company_settings
- **id**: Serial, Primary Key
- **company_name**: VARCHAR(255), Not Null
- **website**: VARCHAR(255)
- **email**: VARCHAR(254), Not Null
- **phone**: VARCHAR(20), Not Null
- **address**: TEXT, Not Null
- **timezone**: VARCHAR(50), Not Null, Default 'UTC'
- **date_format**: VARCHAR(20), Not Null, Default 'YYYY-MM-DD'
- **currency**: VARCHAR(3), Not Null, Default 'USD'
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

#### roles
- **id**: Serial, Primary Key
- **name**: VARCHAR(100), Not Null, Unique
- **description**: TEXT

#### role_permissions
- **id**: Serial, Primary Key
- **role_id**: INTEGER, Foreign Key to roles(id)
- **permission**: VARCHAR(100), Not Null
- **UNIQUE**: (role_id, permission)

#### notification_settings
- **id**: Serial, Primary Key
- **category**: VARCHAR(50), Not Null, Unique
- **email**: BOOLEAN, Default TRUE
- **in_app**: BOOLEAN, Default TRUE
- **sms**: BOOLEAN, Default FALSE

#### integrations
- **id**: Serial, Primary Key
- **name**: VARCHAR(100), Not Null
- **type**: VARCHAR(50), Not Null
- **api_key**: VARCHAR(255)
- **status**: VARCHAR(20), Not Null, Default 'inactive'
- **last_sync**: TIMESTAMP
- **description**: TEXT
- **created_at**: TIMESTAMP, Default CURRENT_TIMESTAMP
- **updated_at**: TIMESTAMP, Default CURRENT_TIMESTAMP

#### integration_tags
- **id**: Serial, Primary Key
- **integration_id**: INTEGER, Foreign Key to integrations(id)
- **key**: VARCHAR(100), Not Null
- **value**: TEXT, Not Null
- **UNIQUE**: (integration_id, key)

## Indexes

The following indexes are created to improve query performance:

- **idx_users_role**: On users(role)
- **idx_users_status**: On users(status)
- **idx_products_category**: On products(category_id)
- **idx_products_status**: On products(status)
- **idx_orders_customer**: On orders(customer_id)
- **idx_orders_status**: On orders(status)
- **idx_orders_date**: On orders(order_date)
- **idx_transactions_customer**: On transactions(customer_id)
- **idx_transactions_status**: On transactions(status)
- **idx_transactions_date**: On transactions(date)
- **idx_transactions_invoice**: On transactions(invoice_id)
- **idx_invoices_customer**: On invoices(customer_id)
- **idx_invoices_status**: On invoices(status)
- **idx_invoices_date**: On invoices(issue_date)
- **idx_reports_type**: On reports(type)
- **idx_reports_date**: On reports(date)
- **idx_reports_status**: On reports(status)

## Relationships

### One-to-Many Relationships

- User → UserDocuments
- User → PaymentMethods
- User → Orders
- User → Transactions
- User → Invoices
- User → Reports (as creator)
- Category → Products
- Warehouse → ProductLocations
- Product → ProductSpecifications
- Product → ProductIncludedItems
- Product → ProductLocations
- Product → MaintenanceRecords
- Product → OrderItems
- Order → OrderItems
- Order → OrderTimeline
- Order → RentalPeriods
- Transaction → TransactionTimeline
- Invoice → InvoiceItems
- Role → RolePermissions
- Integration → IntegrationTags

### Many-to-One Relationships

- UserDocument → User
- PaymentMethod → User
- Product → Category
- ProductSpecification → Product
- ProductIncludedItem → Product
- ProductLocation → Product, Warehouse
- MaintenanceRecord → Product
- Order → User (as customer)
- OrderItem → Order, Product
- DeliveryAddress → Order
- RentalPeriod → Order
- OrderTimeline → Order
- Transaction → User (as customer), Invoice
- TransactionTimeline → Transaction
- Invoice → User (as customer)
- InvoiceItem → Invoice
- BillingAddress → Invoice
- Report → User (as creator)
- RolePermission → Role
- IntegrationTag → Integration

## Data Types

- **VARCHAR**: For string data with variable length
- **TEXT**: For longer string data
- **INTEGER**: For whole numbers
- **DECIMAL**: For monetary values with precision
- **BOOLEAN**: For true/false values
- **DATE**: For date values
- **TIME**: For time values
- **TIMESTAMP**: For date and time values

## Constraints

- **Primary Keys**: Every table has a unique identifier
- **Foreign Keys**: Maintain referential integrity between tables
- **Not Null**: Ensure required fields have values
- **Unique**: Prevent duplicate values in specific fields
- **Default Values**: Provide sensible defaults for fields

## Cascading Actions

- **ON DELETE CASCADE**: When a parent record is deleted, related child records are also deleted
- **ON DELETE SET NULL**: When a parent record is deleted, the foreign key in child records is set to NULL

## Conclusion

This database schema provides a comprehensive foundation for the Go4Rent Dashboard application, supporting all the required functionality including user management, inventory management, order processing, financial operations, reporting, and system settings. The schema is designed with performance, data integrity, and scalability in mind.
