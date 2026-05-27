# Engineering Decisions

## Data Source Choices

### 1. SAP Export Format: CSV Flat File

**Decision**: Use CSV exports from SAP ERP rather than IDoc, OData, or BAPI.

**Reasoning**:

- Most ESG onboarding workflows start with manual exports before API integrations
- CSV is universally supported across SAP versions
- Lower technical barrier for client sustainability teams
- Easier to debug and validate during initial onboarding

**Tradeoffs**:

- No real-time sync (batch-oriented)
- Manual export process required
- Potential for human error in export configuration

**What I'd ask the PM**:

- Do clients have SAP BW/BI access for automated extracts?
- What's the typical data refresh cadence (monthly, quarterly)?
- Are there specific SAP modules we need to support (MM, FI, CO)?

**Subset Handled**:

- Material master data (fuel types)
- Posting documents with quantities and units
- Plant/location codes
- Vendor information

**Ignored**:

- Complex procurement hierarchies
- Multi-currency conversions beyond basic rates
- SAP workflow approvals
- Historical data migrations (>2 years)

### 2. Utility Data: Portal CSV Exports

**Decision**: Support CSV exports from utility web portals rather than PDF parsing or direct API integration.

**Reasoning**:

- Most utilities provide CSV download functionality
- PDF parsing is brittle and error-prone (OCR, layout variations)
- Direct utility APIs are rare and require per-utility integration
- CSV format is consistent enough across providers

**Tradeoffs**:

- Manual download process
- Billing period misalignment with calendar months
- Inconsistent column naming across utilities

**What I'd ask the PM**:

- How many different utility providers do clients typically use?
- Is there a preferred utility aggregation service (UtilityAPI, Urjanet)?
- Should we support interval data (15-min readings) or just monthly totals?

**Subset Handled**:

- Total kWh consumption
- Billing period dates
- Meter IDs and facility mapping
- Peak/off-peak breakdowns (optional)

**Ignored**:

- Demand charges and tariff complexity
- Power factor and reactive power
- Interval data (sub-hourly)
- Solar generation offsets

### 3. Corporate Travel: Concur-style CSV Export

**Decision**: Model after Concur/Navan export formats with flight, hotel, and ground transport categories.

**Reasoning**:

- Concur and Navan dominate enterprise travel management
- Export formats are relatively standardized
- Covers 80% of Scope 3 travel emissions

**Tradeoffs**:

- Distance data often missing (requires estimation)
- Travel class impacts emission factors significantly
- Hotel emissions are approximations (no energy data)

**What I'd ask the PM**:

- Do clients use Concur, Navan, SAP Concur, or other platforms?
- Should we integrate with GDS (Amadeus, Sabre) for richer data?
- How important is rail travel (varies by region)?

**Subset Handled**:

- Flights with origin/destination airports
- Hotel nights
- Ground transport (taxi, rental car)
- Basic distance estimation

**Ignored**:

- Rail travel (significant in Europe/Asia)
- Ferry/cruise emissions
- Commuting (employee-owned vehicles)
- Detailed aircraft type and load factors

## Architecture Decisions

### 4. Async File Processing

**Decision**: Process uploaded files asynchronously using Python threading.

**Reasoning**:

- Large CSV files (10k+ rows) can take 30+ seconds to process
- Synchronous processing blocks the upload API response
- Users need immediate feedback that upload succeeded

**Tradeoffs**:

- Threading (not Celery) limits scalability
- No distributed task queue
- Error handling requires polling or notifications

**What I'd ask the PM**:

- What's the largest expected file size (rows)?
- Is real-time processing feedback required?
- Should we support scheduled/recurring imports?

**Production Alternative**: Use Celery + Redis for distributed task processing.

### 5. Raw Data Preservation

**Decision**: Store original uploaded data in RawRecord.raw_payload as JSON.

**Reasoning**:

- Enables re-processing if normalization logic changes
- Audit requirement: prove what was originally submitted
- Debugging: compare raw vs. normalized data

**Tradeoffs**:

- Storage overhead (2x data: raw + normalized)
- JSON queries are slower than relational columns

**What I'd ask the PM**:

- How long must raw data be retained (compliance)?
- Should we support data lineage visualization?

### 6. Suspicious Data Flagging

**Decision**: Automatically flag records with anomalies but don't block ingestion.

**Reasoning**:

- False positives are common (legitimate high usage)
- Analysts need to see all data, not just "clean" data
- Flagging enables prioritized review

**Tradeoffs**:

- Simple heuristics miss sophisticated anomalies
- Requires analyst judgment (not fully automated)

**What I'd ask the PM**:

- Should we use ML-based anomaly detection?
- What's the acceptable false positive rate?
- Should flagged records require mandatory review?

**Current Heuristics**:

- Quantity ≤ 0
- Quantity > 1,000,000
- Future activity dates
- Missing units

**Ignored**:

- Statistical outliers (z-score, IQR)
- Duplicate detection across sources
- Temporal anomalies (sudden spikes)

### 7. Emission Factor Hardcoding

**Decision**: Hardcode emission factors in Python rather than database-driven configuration.

**Reasoning**:

- Emission factors change infrequently (annually)
- Simplifies initial implementation
- Avoids complex factor selection logic

**Tradeoffs**:

- Requires code deployment to update factors
- No regional variation support
- No client-specific factors

**What I'd ask the PM**:

- Do clients use custom emission factors?
- Should we support multiple factor databases (EPA, DEFRA, GHG Protocol)?
- How often do factors need updating?

**Production Alternative**: Database-driven EmissionFactor model with versioning and regional support.

### 8. Role-Based Access Control

**Decision**: Three roles: Admin, Analyst, Viewer.

**Reasoning**:

- Covers common enterprise access patterns
- Simple to implement and explain
- Aligns with audit separation of duties

**Tradeoffs**:

- No fine-grained permissions (e.g., approve but not edit)
- No custom role creation

**What I'd ask the PM**:

- Do clients need custom roles?
- Should approval require dual authorization?
- Are there regional access restrictions (GDPR)?

### 9. Audit Lock Mechanism

**Decision**: Approved records can be locked by admins, preventing further changes.

**Reasoning**:

- Audit compliance: data submitted to auditors must be immutable
- Prevents accidental modifications
- Clear workflow: review → approve → lock → audit

**Tradeoffs**:

- No unlock mechanism (requires admin intervention)
- Locked records can't be corrected if errors found

**What I'd ask the PM**:

- Should locked records be unlockable (with audit trail)?
- What triggers lock (manual, time-based, audit submission)?
- Should locking be automatic after approval?

### 10. Frontend State Management: Zustand

**Decision**: Use Zustand for auth state, React Query for server state.

**Reasoning**:

- Zustand is lightweight and simple for auth
- React Query handles caching, refetching, and loading states
- Avoids Redux boilerplate

**Tradeoffs**:

- Less ecosystem support than Redux
- No time-travel debugging

## Technology Stack Decisions

### 11. Django REST Framework

**Decision**: Use DRF for API layer.

**Reasoning**:

- Mature, well-documented
- Built-in serialization, validation, pagination
- Excellent for CRUD-heavy applications

**Tradeoffs**:

- Heavier than FastAPI
- Synchronous by default (async support limited)

### 12. PostgreSQL

**Decision**: Use PostgreSQL as primary database.

**Reasoning**:

- ACID compliance for audit trail
- JSON support for flexible metadata
- Excellent indexing and query performance
- Wide deployment support (Render, Railway, AWS RDS)

**Tradeoffs**:

- More complex than SQLite for local dev
- Requires managed service for production

### 13. React + Vite

**Decision**: Use React with Vite for frontend.

**Reasoning**:

- Fast development experience
- Modern build tooling
- Smaller bundle sizes than Create React App

**Tradeoffs**:

- Less mature than CRA
- Fewer plugins/templates

### 14. Tailwind CSS

**Decision**: Use Tailwind for styling.

**Reasoning**:

- Rapid UI development
- Consistent design system
- No CSS file management

**Tradeoffs**:

- Verbose className attributes
- Learning curve for non-Tailwind developers

## Deployment Decisions

### 15. Separate Backend/Frontend Deployment

**Decision**: Deploy backend (Render/Railway) and frontend (Vercel/Netlify) separately.

**Reasoning**:

- Independent scaling
- Faster frontend deployments (no backend rebuild)
- CDN benefits for static frontend

**Tradeoffs**:

- CORS configuration required
- Two deployment pipelines

**What I'd ask the PM**:

- Is there a preferred cloud provider (AWS, GCP, Azure)?
- Should we use Docker containers?
- What's the expected traffic (concurrent users)?

## What I Deliberately Ignored

1. **Authentication**: No OAuth, SSO, or MFA (would use Auth0/Okta in production)
2. **Email Notifications**: No email alerts for approvals (would use SendGrid/SES)
3. **File Validation**: No pre-upload schema validation (would add JSON Schema validation)
4. **Bulk Edit**: No bulk edit functionality (only bulk approve)
5. **Export**: No CSV/Excel export of reviewed data (would add for reporting)
6. **Search**: Basic search only (would add Elasticsearch for full-text search)
7. **Versioning**: No record versioning (audit log provides history but not rollback)
8. **Webhooks**: No webhook support for external integrations
9. **Rate Limiting**: No API rate limiting (would add for production)
10. **Monitoring**: No APM or error tracking (would add Sentry/DataDog)
