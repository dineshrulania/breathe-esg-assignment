# Data Source Research & Implementation

## Source 1: SAP Export (Fuel & Procurement)

### Real-World Format Research

**What I Researched**:

- SAP ERP Material Management (MM) and Financial Accounting (FI) modules
- Common export mechanisms: IDoc, BAPI, OData, flat file CSV
- Typical data structures for fuel procurement and material movements

**Key Findings**:

1. **Export Methods**:
   - **IDoc (Intermediate Document)**: XML-based, complex structure, requires SAP PI/PO
   - **BAPI (Business API)**: Programmatic access, requires SAP credentials and network access
   - **OData**: RESTful API, modern but not universally available
   - **Flat File CSV**: Most common for manual exports, generated via SE16/SE16N or custom reports

2. **Column Naming**:
   - SAP systems often have German column names (Werk, Menge, Einheit, Buchungsdatum)
   - English translations vary by configuration
   - Plant codes are cryptic (P001, WERK_DE_01) and require lookup tables

3. **Data Challenges**:
   - Units are inconsistent (L, LTR, Liters, l)
   - Material descriptions contain fuel type but require parsing
   - Posting dates can be in multiple formats (YYYYMMDD, DD.MM.YYYY, DD/MM/YYYY)
   - Vendor codes are numeric IDs, not human-readable names

### Sample Data Design

**Why It Looks This Way**:

```csv
Plant_Code,Material_Number,Material_Description,Quantity,Unit,Posting_Date,Vendor,Document_Number
P001,MAT-1001,Diesel Fuel Industrial Grade,5000,L,2024-01-15,Shell Energy,DOC-2024-001
```

- **Plant_Code**: Realistic SAP plant codes (P001, P002) representing facilities
- **Material_Number**: SAP material master format (MAT-XXXX)
- **Material_Description**: Contains fuel type keywords for parsing (Diesel, Petrol, Natural Gas)
- **Quantity**: Realistic fuel volumes (thousands of liters for industrial use)
- **Unit**: Varied units (L, M3, KG) to test normalization
- **Posting_Date**: ISO format for simplicity (real SAP exports vary)
- **Vendor**: Human-readable names (real SAP uses vendor codes)
- **Document_Number**: SAP document reference format

**What Would Break in Production**:

1. **German Column Names**: Real exports often have "Werk" instead of "Plant_Code"
   - **Fix**: Add column name mapping dictionary
2. **Material Master Complexity**: Real material descriptions are cryptic ("FUEL-DIE-IND-50L")
   - **Fix**: Maintain material master lookup table or use ML classification
3. **Plant Code Lookup**: Plant codes don't indicate location without reference data
   - **Fix**: Integrate with SAP plant master data or maintain manual mapping
4. **Multi-Currency**: Procurement data includes costs in various currencies
   - **Fix**: Add currency conversion logic
5. **Batch Numbers**: Real SAP exports include batch/lot numbers for traceability
   - **Fix**: Extend metadata to capture batch information
6. **Movement Types**: SAP has 100+ movement types (goods receipt, transfer, consumption)
   - **Fix**: Filter by relevant movement types (201, 261 for consumption)

### Implementation Decisions

**Chosen Approach**: CSV flat file upload

- **Justification**: Most ESG teams start with manual exports before API integration
- **Tradeoff**: No real-time sync, manual process

**Normalization Logic**:

- Parse material description for fuel type keywords
- Convert units to standard (liters for volume, kg for mass)
- Classify as Scope 1 (direct fuel combustion)
- Apply emission factors based on fuel type

**Ignored Complexity**:

- Multi-plant consolidation
- Procurement vs. consumption distinction
- Cost allocation and internal transfers
- Historical data migration

---

## Source 2: Utility Data (Electricity)

### Real-World Format Research

**What I Researched**:

- Utility web portal CSV exports (PG&E, ConEd, National Grid)
- Utility API providers (UtilityAPI, Urjanet, Genability)
- Green Button data standard (XML format for energy data)

**Key Findings**:

1. **Portal Exports**:
   - Most utilities provide CSV download from web portals
   - Formats vary significantly across providers
   - Typically include: meter ID, billing period, total kWh, charges
   - Some include interval data (15-min or hourly readings)

2. **Billing Period Challenges**:
   - Billing periods rarely align with calendar months
   - Example: Jan 15 - Feb 14 (not Jan 1 - Jan 31)
   - Requires period normalization for monthly reporting

3. **Tariff Complexity**:
   - Time-of-use (TOU) tariffs: peak, off-peak, super off-peak
   - Demand charges based on peak kW (not kWh)
   - Tiered pricing (first 500 kWh at rate A, next 500 at rate B)
   - Seasonal variations (summer vs. winter rates)

4. **Meter Mapping**:
   - Large facilities have multiple meters
   - Meter IDs are utility-specific (not standardized)
   - Mapping meters to facilities/cost centers is manual

### Sample Data Design

**Why It Looks This Way**:

```csv
Meter_ID,Facility_Name,Billing_Period_Start,Billing_Period_End,Total_kWh,Peak_Usage_kWh,Off_Peak_Usage_kWh,Tariff_Type
MTR-001,Headquarters Building,2024-01-01,2024-01-31,45000,28000,17000,Commercial
```

- **Meter_ID**: Realistic meter identifier format
- **Facility_Name**: Human-readable facility names (real systems use codes)
- **Billing_Period_Start/End**: Date range (real periods don't align with months)
- **Total_kWh**: Realistic commercial building consumption (30-50k kWh/month)
- **Peak/Off_Peak**: TOU breakdown (optional but common)
- **Tariff_Type**: Commercial vs. Industrial (affects emission factors in some regions)

**What Would Break in Production**:

1. **Misaligned Billing Periods**: Real periods span month boundaries
   - **Fix**: Prorate consumption to calendar months or report by billing period
2. **Missing Facility Mapping**: Meter IDs don't indicate location
   - **Fix**: Maintain meter-to-facility lookup table
3. **Demand Charges**: kW demand is separate from kWh consumption
   - **Fix**: Add demand fields and separate emission calculation
4. **Solar Offsets**: Net metering shows negative consumption
   - **Fix**: Separate grid consumption from solar generation
5. **Multiple Utilities**: Large companies have accounts with 10+ utilities
   - **Fix**: Add utility provider field and provider-specific parsing
6. **Interval Data**: 15-minute readings create 2,880 rows/meter/month
   - **Fix**: Aggregate to daily or monthly totals for ESG reporting

### Implementation Decisions

**Chosen Approach**: CSV portal export

- **Justification**: Most accessible format, no API credentials required
- **Tradeoff**: Manual download, no automation

**Normalization Logic**:

- Use billing period start date as activity date
- Total kWh is already in standard unit
- Classify as Scope 2 (purchased electricity)
- Apply grid emission factor (0.385 kg CO2e/kWh - US average)

**Ignored Complexity**:

- Renewable energy certificates (RECs)
- Location-based vs. market-based emission factors
- Demand charges and power factor
- Interval data aggregation

---

## Source 3: Corporate Travel

### Real-World Format Research

**What I Researched**:

- Concur (SAP Concur) export formats
- Navan (formerly TripActions) API documentation
- GDS (Global Distribution System) data: Amadeus, Sabre
- IATA airport codes and distance calculation

**Key Findings**:

1. **Travel Platform Exports**:
   - Concur provides CSV exports with booking details
   - Includes: traveler, dates, origin/destination, travel class, cost
   - Often missing: actual distance flown, aircraft type, load factor

2. **Flight Data Challenges**:
   - Airport codes (IATA 3-letter) provided, but distance often missing
   - Distance calculation requires great circle distance (haversine formula)
   - Emission factors vary by:
     - Flight distance (short <1500km, medium 1500-4000km, long >4000km)
     - Travel class (economy, business, first)
     - Aircraft type (not usually available)
     - Load factor (passengers / capacity)

3. **Hotel Emissions**:
   - No energy data available from booking systems
   - Emission factors are per-night averages
   - Vary by hotel type (budget, luxury) and region
   - Highly uncertain (±50%)

4. **Ground Transport**:
   - Taxi/rideshare: distance often missing
   - Rental cars: distance from odometer (if returned to same location)
   - Rail: distance calculable from stations, but emission factors vary by country

### Sample Data Design

**Why It Looks This Way**:

```csv
Traveler_Name,Travel_Date,Transport_Type,Origin,Destination,Distance_km,Travel_Class,Hotel_Nights
John Smith,2024-01-10,Flight,JFK,LAX,3983,Economy,
Sarah Johnson,2024-01-10,Hotel,,,,,3
```

- **Traveler_Name**: Anonymized employee names
- **Travel_Date**: Booking or travel date
- **Transport_Type**: Flight, Hotel, Taxi, Car Rental, Rail
- **Origin/Destination**: IATA airport codes for flights
- **Distance_km**: Provided when available (often missing)
- **Travel_Class**: Economy, Business, First (affects emission factor)
- **Hotel_Nights**: Number of nights for accommodation

**What Would Break in Production**:

1. **Missing Distance Data**: 60% of bookings don't include distance
   - **Fix**: Calculate from airport codes using haversine formula or lookup table
2. **Multi-Leg Flights**: JFK→LHR→DXB reported as single trip
   - **Fix**: Parse itinerary to extract individual legs
3. **Connecting Flights**: Layovers vs. direct flights have different emissions
   - **Fix**: Use radiative forcing index (RFI) for high-altitude emissions
4. **Rail Travel**: Significant in Europe/Asia, minimal in US
   - **Fix**: Add rail-specific emission factors by region
5. **Commuting**: Employee-owned vehicle travel not captured
   - **Fix**: Separate data source for commuting surveys
6. **Travel Class Upgrades**: Booked economy, upgraded to business
   - **Fix**: Use actual travel class from boarding pass data (if available)

### Implementation Decisions

**Chosen Approach**: CSV export from travel platform

- **Justification**: Concur/Navan provide standardized exports
- **Tradeoff**: Missing granular data (aircraft type, actual distance)

**Normalization Logic**:

- Classify flights by distance (short/medium/long haul)
- Apply distance-based emission factors
- Hotel emissions: fixed per-night factor
- Ground transport: distance-based factors
- All classified as Scope 3 (indirect emissions)

**Distance Estimation**:

- Hardcoded lookup table for common routes
- Fallback: 1000 km default (conservative estimate)
- Production would use haversine formula or GeoNames API

**Ignored Complexity**:

- Radiative forcing (high-altitude emissions multiplier)
- Aircraft type and load factor
- Sustainable aviation fuel (SAF) offsets
- Rail travel (not in sample data)
- Commuting and remote work emissions

---

## Cross-Source Challenges

### 1. Date Format Inconsistency

- SAP: YYYYMMDD or DD.MM.YYYY
- Utility: YYYY-MM-DD or MM/DD/YYYY
- Travel: ISO 8601 or locale-specific

**Solution**: Use dateutil.parser for flexible parsing

### 2. Unit Variations

- Volume: L, LTR, Liters, l, gallons, m3
- Energy: kWh, MWh, GJ, kJ
- Distance: km, miles, meters

**Solution**: Normalization lookup table with conversion factors

### 3. Missing Data

- SAP: Vendor names often just codes
- Utility: Facility mapping requires manual lookup
- Travel: Distance frequently missing

**Solution**: Store original data, flag missing fields, allow manual enrichment

### 4. Duplicate Detection

- Same fuel delivery recorded in SAP and invoice system
- Utility bill uploaded twice (different formats)
- Travel booking amended (original + updated record)

**Solution**: Not implemented (would require fuzzy matching on date + quantity + source)

---

## Production Readiness Assessment

### What Works Now

✅ Handles realistic CSV formats
✅ Normalizes common units
✅ Classifies emission scopes correctly
✅ Flags obvious data quality issues
✅ Preserves raw data for audit

### What Needs Work

❌ Column name mapping (hardcoded English names)
❌ Distance calculation (uses lookup table, not haversine)
❌ Duplicate detection (not implemented)
❌ Multi-currency support (not implemented)
❌ Regional emission factors (uses global averages)
❌ Interval data aggregation (not supported)
❌ Multi-leg flight parsing (not implemented)

### Estimated Production Readiness: 70%

**To reach 90%**:

- Add flexible column mapping UI
- Implement haversine distance calculation
- Add duplicate detection logic
- Support regional emission factor databases
- Add data enrichment APIs (airport lookup, currency conversion)

**To reach 100%**:

- Support all SAP export formats (IDoc, OData)
- Integrate with utility APIs (UtilityAPI, Urjanet)
- Direct integration with Concur/Navan APIs
- ML-based data quality scoring
- Automated facility/meter mapping
