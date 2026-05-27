# Data Model Documentation

## Overview

The ESG Platform data model is designed to handle multi-tenant enterprise ESG data ingestion, normalization, review workflows, and audit compliance. The architecture prioritizes data provenance, auditability, and scalability.

## Core Design Principles

1. **Source-of-Truth Tracking**: Every normalized record maintains a link to its raw source
2. **Immutability After Audit Lock**: Approved and locked records cannot be modified
3. **Complete Audit Trail**: All changes are logged with user attribution and timestamps
4. **Multi-Tenancy**: Company-level data isolation for enterprise clients
5. **Flexible Normalization**: Support for various units, formats, and emission factors

## Entity Relationship Model

### Company

- **Purpose**: Multi-tenant organization container
- **Key Fields**: name, created_at, is_active
- **Relationships**: Has many Users, DataSources, EmissionRecords

### User (extends Django AbstractUser)

- **Purpose**: Authentication and role-based access control
- **Key Fields**: username, email, company, role (admin/analyst/viewer)
- **Relationships**: Belongs to Company, creates DataSources, approves EmissionRecords

### DataSource

- **Purpose**: Tracks file uploads and processing status
- **Key Fields**:
  - source_type: sap, utility, travel
  - upload_method: csv, api, manual
  - processing_status: pending, processing, completed, failed
  - total_rows, processed_rows, failed_rows
- **Relationships**: Belongs to Company, has many RawRecords and NormalizedEmissionRecords
- **Design Decision**: Separate tracking of upload metadata from actual data enables async processing and detailed error reporting

### RawRecord

- **Purpose**: Preserves original uploaded data without modification
- **Key Fields**:
  - raw_payload: JSONField storing original row data
  - validation_status: valid, invalid, warning
  - validation_errors: Array of error messages
- **Relationships**: Belongs to DataSource, has one NormalizedEmissionRecord
- **Design Decision**: Storing raw data as JSON provides flexibility for varying source schemas without schema migrations

### NormalizedEmissionRecord

- **Purpose**: Core business entity representing a single emission activity
- **Key Fields**:
  - **Scope Classification**: scope (scope_1/2/3), category, activity_type
  - **Quantity**: quantity, normalized_unit, original_unit
  - **Emissions**: emission_factor, emission_value, emission_unit
  - **Location**: location, facility, vendor
  - **Review**: status (pending/approved/rejected/flagged), suspicious_flag, suspicious_reason
  - **Audit**: approved_by, approved_at, locked_for_audit
  - **Metadata**: notes, metadata (JSON for extensibility)
- **Relationships**: Belongs to Company, DataSource, RawRecord; has many AuditLogs
- **Indexes**:
  - (company, status) - Fast filtering for review dashboards
  - (scope, activity_date) - Efficient reporting queries
  - (suspicious_flag) - Quick access to flagged records

### AuditLog

- **Purpose**: Immutable record of all changes to emission records
- **Key Fields**:
  - action: create, update, approve, reject, flag, lock, unlock
  - changed_by: User who made the change
  - old_value, new_value: JSON snapshots of record state
  - notes: Optional explanation
- **Relationships**: Belongs to NormalizedEmissionRecord and User
- **Design Decision**: Storing full snapshots (not diffs) simplifies audit queries and compliance reporting

### Notification

- **Purpose**: User notifications for processing events
- **Key Fields**: notification_type, message, read status
- **Relationships**: Belongs to User

### UnitConversion

- **Purpose**: Lookup table for unit normalization
- **Key Fields**: from_unit, to_unit, conversion_factor, category
- **Design Decision**: Separate table allows runtime updates without code deployment

### EmissionFactor

- **Purpose**: Emission calculation coefficients
- **Key Fields**: activity_type, scope, factor_value, unit, source, year, region
- **Design Decision**: Versioned by year and region for compliance with evolving standards

## Normalization Strategy

### Unit Normalization

All quantities are converted to standard units:

- Energy: kWh
- Volume: liters
- Mass: kg
- Distance: km

Conversion factors are applied during ingestion, with both original and normalized values stored.

### Date Normalization

Multiple date formats are parsed using dateutil.parser:

- ISO 8601
- DD/MM/YYYY
- MM/DD/YYYY
- German formats (DD.MM.YYYY)

### Scope Classification

Automatic scope assignment based on activity type:

- Scope 1: Direct emissions (fuel combustion)
- Scope 2: Purchased electricity
- Scope 3: Indirect emissions (travel, procurement)

## Suspicious Data Detection

Records are automatically flagged if they exhibit:

- Zero or negative quantities
- Unusually high values (>1,000,000 units)
- Future activity dates
- Missing critical fields (units, dates)

Flagged records require explicit analyst review before approval.

## Audit Trail Strategy

Every state change creates an AuditLog entry:

1. **Record Creation**: Initial ingestion
2. **Updates**: Field modifications by analysts
3. **Approval/Rejection**: Status changes with user attribution
4. **Locking**: Final audit lock preventing further changes

Audit logs are append-only and never deleted, ensuring complete compliance history.

## Multi-Tenancy Implementation

Company-level isolation is enforced at:

1. **Database Level**: Foreign key relationships
2. **API Level**: QuerySet filtering based on user.company
3. **Permission Level**: Role-based access control

Admin users can access all companies; analysts and viewers are restricted to their own company.

## Scaling Considerations

### Current Architecture

- PostgreSQL for relational integrity
- Indexed queries for common access patterns
- Async file processing to avoid blocking uploads

### Future Scaling Paths

1. **Read Replicas**: Separate analytics queries from transactional workload
2. **Partitioning**: Partition NormalizedEmissionRecord by company_id or activity_date
3. **Caching**: Redis for dashboard statistics
4. **Archival**: Move locked records older than N years to cold storage
5. **Sharding**: Horizontal partitioning by company for very large deployments

## Schema Evolution Strategy

The metadata JSONField in NormalizedEmissionRecord provides extensibility without migrations:

- Source-specific fields (SAP document numbers, meter IDs)
- Custom client fields
- Future emission calculation parameters

This allows onboarding new clients with unique requirements without schema changes.

## Compliance & Audit Requirements

The model satisfies:

- **GHG Protocol**: Scope 1/2/3 classification
- **ISO 14064**: Activity-based accounting with emission factors
- **Audit Trail**: Complete change history with user attribution
- **Data Provenance**: Raw data preservation and source tracking
- **Immutability**: Locked records cannot be altered

## Performance Characteristics

Typical query patterns:

- Dashboard stats: <100ms (indexed aggregations)
- Review queue: <200ms (filtered by status, paginated)
- Record details: <50ms (single row lookup with joins)
- Audit logs: <150ms (filtered by record_id)

Bottlenecks:

- File processing: O(n) where n = row count (async to avoid blocking)
- Bulk approval: O(n) where n = selected records (acceptable for <1000 records)
