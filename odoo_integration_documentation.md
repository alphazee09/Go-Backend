# Odoo Integration Documentation for Go4Rent Dashboard

## Overview

This document provides comprehensive documentation for the Odoo integration functionality implemented in the Go4Rent Dashboard application. The integration allows for bidirectional synchronization of data between Go4Rent and Odoo ERP system.

## Features

The Odoo integration provides the following key features:

1. **Bidirectional Synchronization**: Data can be synchronized in both directions:
   - Export: From Go4Rent to Odoo
   - Import: From Odoo to Go4Rent

2. **Multiple Entity Support**: The integration supports synchronization of:
   - Products/Inventory
   - Customers/Users
   - Orders/Rentals
   - Invoices/Billing

3. **Flexible Configuration**: Each integration can be configured with:
   - Connection settings (URL, database, credentials)
   - Sync preferences (which entities to sync)
   - Sync intervals (how often to sync each entity)

4. **Detailed Logging**: All synchronization operations are logged with:
   - Success/failure status
   - Records processed, succeeded, and failed
   - Detailed error messages
   - Timestamps for audit trails

5. **API Endpoints**: RESTful API endpoints for:
   - Managing integration settings
   - Testing connections
   - Triggering manual synchronization
   - Viewing sync logs

## Architecture

### Database Models

The integration is built on the following database models:

1. **OdooIntegration**: Stores connection settings and sync preferences
   - Links to a base Integration record
   - Contains connection details (URL, database, credentials)
   - Stores sync preferences and intervals
   - Tracks last sync timestamps

2. **Mapping Tables**: Track relationships between Go4Rent and Odoo records
   - OdooProductMapping
   - OdooCustomerMapping
   - OdooOrderMapping
   - OdooInvoiceMapping

3. **OdooSyncLog**: Records details of each synchronization operation
   - Tracks sync type, direction, and status
   - Counts records processed, succeeded, and failed
   - Stores error messages and detailed results

### Service Layer

The integration uses a service-oriented architecture:

1. **OdooClient**: Handles low-level communication with Odoo
   - Manages authentication
   - Provides methods for CRUD operations
   - Handles error conditions

2. **OdooSyncService**: Implements business logic for synchronization
   - Manages bidirectional sync for each entity type
   - Handles mapping between Go4Rent and Odoo data models
   - Creates and updates records in both systems
   - Logs synchronization results

### API Layer

The integration exposes RESTful API endpoints:

1. **OdooIntegrationViewSet**: Manages integration settings
   - CRUD operations for integration records
   - Test connection functionality
   - Endpoints for triggering synchronization

2. **OdooSyncLogViewSet**: Provides access to sync logs
   - Read-only access to log records
   - Filtering by various criteria

## Implementation Details

### Data Mapping

The integration maps data between Go4Rent and Odoo as follows:

#### Products

| Go4Rent Field | Odoo Field |
|---------------|------------|
| id | x_go4rent_id |
| id_code | x_go4rent_id_code |
| name | name |
| sku | default_code |
| rental_price | list_price |
| replacement_value | standard_price |
| description | description |

#### Customers

| Go4Rent Field | Odoo Field |
|---------------|------------|
| id | x_go4rent_id |
| first_name + last_name | name |
| email | email |
| phone | phone |
| address | street |

#### Orders

| Go4Rent Field | Odoo Field |
|---------------|------------|
| id | x_go4rent_id |
| id_code | x_go4rent_id_code, client_order_ref |
| customer | partner_id |
| order_date | date_order |
| status | state (mapped) |
| notes | note |

#### Invoices

| Go4Rent Field | Odoo Field |
|---------------|------------|
| id | x_go4rent_id |
| id_code | x_go4rent_id_code, ref |
| number | name |
| customer | partner_id |
| issue_date | invoice_date |
| due_date | invoice_date_due |
| status | state (mapped) |
| notes | narration |

### Status Mapping

The integration maps status values between the two systems:

#### Order Status

| Go4Rent Status | Odoo Status |
|----------------|-------------|
| pending | draft |
| confirmed | sent |
| in_progress | sale |
| completed | done |
| cancelled | cancel |

#### Invoice Status

| Go4Rent Status | Odoo Status |
|----------------|-------------|
| draft | draft |
| sent | posted |
| paid | paid |
| partial | partial |
| overdue | posted |
| cancelled | cancel |

### Synchronization Process

The synchronization process follows these steps:

1. **Export (Go4Rent to Odoo)**:
   - Identify records to sync (new or updated since last sync)
   - For each record:
     - Check if it exists in Odoo (via mapping table)
     - If exists, update the Odoo record
     - If not, create a new Odoo record
     - Update the mapping table
   - Update last sync timestamp

2. **Import (Odoo to Go4Rent)**:
   - Identify records to sync (new or updated since last sync)
   - For each record:
     - Check if it exists in Go4Rent (via mapping table)
     - If exists, update the Go4Rent record
     - If not, create a new Go4Rent record
     - Update the mapping table
   - Update last sync timestamp

### Error Handling

The integration implements robust error handling:

1. **Connection Errors**: Detected and logged during connection attempts
2. **Authentication Errors**: Handled during client initialization
3. **Record-Level Errors**: Caught and logged for individual records
4. **Transaction Management**: Uses Django's transaction management to ensure data integrity

## API Endpoints

### Integration Management

- `GET /api/odoo/odoo-integrations/`: List all Odoo integrations
- `POST /api/odoo/odoo-integrations/`: Create a new Odoo integration
- `GET /api/odoo/odoo-integrations/{id}/`: Get a specific Odoo integration
- `PUT /api/odoo/odoo-integrations/{id}/`: Update an Odoo integration
- `DELETE /api/odoo/odoo-integrations/{id}/`: Delete an Odoo integration

### Connection Testing

- `POST /api/odoo/odoo-integrations/{id}/test_connection/`: Test connection to Odoo

### Synchronization

- `POST /api/odoo/odoo-integrations/{id}/sync_products/`: Sync products
- `POST /api/odoo/odoo-integrations/{id}/sync_customers/`: Sync customers
- `POST /api/odoo/odoo-integrations/{id}/sync_orders/`: Sync orders
- `POST /api/odoo/odoo-integrations/{id}/sync_invoices/`: Sync invoices
- `POST /api/odoo/odoo-integrations/{id}/sync_all/`: Sync all entities

### Logs

- `GET /api/odoo/odoo-sync-logs/`: List all sync logs
- `GET /api/odoo/odoo-sync-logs/{id}/`: Get a specific sync log

## Frontend Integration

The frontend provides the following API functions for interacting with the Odoo integration:

```typescript
// Get all Odoo integrations
getOdooIntegrations(): Promise<any[]>

// Get a specific Odoo integration
getOdooIntegrationById(id: string): Promise<any>

// Create a new Odoo integration
createOdooIntegration(integrationData: any): Promise<any>

// Update an Odoo integration
updateOdooIntegration(id: string, integrationData: any): Promise<any>

// Delete an Odoo integration
deleteOdooIntegration(id: string): Promise<any>

// Test connection to Odoo
testOdooConnection(id: string): Promise<any>

// Sync products
syncOdooProducts(id: string, direction?: string): Promise<any>

// Sync customers
syncOdooCustomers(id: string, direction?: string): Promise<any>

// Sync orders
syncOdooOrders(id: string, direction?: string): Promise<any>

// Sync invoices
syncOdooInvoices(id: string, direction?: string): Promise<any>

// Sync all entities
syncOdooAll(id: string, direction?: string): Promise<any>

// Get sync logs
getOdooSyncLogs(filters?: any): Promise<any[]>

// Get a specific sync log
getOdooSyncLogById(id: string): Promise<any>
```

## Configuration

To set up a new Odoo integration:

1. Create a new integration record with:
   - URL: The base URL of the Odoo instance (e.g., `https://example.odoo.com`)
   - Database: The Odoo database name
   - Username: Odoo username with API access
   - API Key: Odoo API key or password
   - Company ID: Odoo company ID (usually 1 for single-company instances)
   - Version: Odoo version (e.g., "16.0")

2. Configure sync preferences:
   - Select which entities to sync
   - Set sync intervals for each entity

3. Test the connection to ensure credentials are correct

4. Perform initial synchronization to establish mappings

## Security Considerations

1. **Credentials**: API keys are stored securely and not exposed in API responses
2. **Authentication**: All API endpoints require authentication
3. **Authorization**: Only authorized users can manage integrations
4. **Data Validation**: All input data is validated before processing

## Troubleshooting

Common issues and solutions:

1. **Connection Failures**:
   - Check URL format (should include protocol)
   - Verify database name
   - Ensure username and API key are correct
   - Check network connectivity and firewall settings

2. **Synchronization Errors**:
   - Review sync logs for specific error messages
   - Check for data validation issues
   - Verify that required fields are present in both systems
   - Ensure proper permissions in Odoo

3. **Performance Issues**:
   - Adjust sync intervals to reduce load
   - Implement incremental syncs for large datasets
   - Monitor database performance during sync operations

## Conclusion

The Odoo integration provides a robust, flexible solution for synchronizing data between Go4Rent and Odoo ERP systems. With bidirectional synchronization of products, customers, orders, and invoices, it enables seamless operation across both platforms while maintaining data integrity and providing detailed audit trails.
