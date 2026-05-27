# Breathe ESG Platform

Enterprise ESG data ingestion, normalization, and audit platform built with Django and React.

## Overview

This platform solves the core challenge of ESG data management: ingesting emissions and activity data from disparate enterprise systems (SAP, utility portals, travel platforms), normalizing it into a consistent schema, and providing analyst review workflows before audit submission.

## Features

### Data Ingestion

- **SAP Export Processing**: Fuel and procurement data from SAP ERP
- **Utility Data Import**: Electricity consumption from utility portal CSVs
- **Corporate Travel**: Flight, hotel, and ground transport emissions
- **Async Processing**: Non-blocking file uploads with background processing
- **Raw Data Preservation**: Original data stored for audit and reprocessing

### Data Normalization

- **Unit Conversion**: Automatic normalization to standard units (kWh, liters, kg, km)
- **Scope Classification**: Automatic GHG Protocol Scope 1/2/3 assignment
- **Emission Calculation**: Activity-based emissions using standard factors
- **Date Parsing**: Flexible date format handling

### Review Workflow

- **Suspicious Data Detection**: Automatic flagging of anomalies
- **Analyst Dashboard**: Filterable review queue with bulk actions
- **Approval Workflow**: Approve, reject, or flag records for review
- **Audit Lock**: Immutable records after approval and lock

### Audit & Compliance

- **Complete Audit Trail**: Every change logged with user attribution
- **Source Tracking**: Full provenance from raw upload to normalized record
- **Multi-Tenancy**: Company-level data isolation
- **Role-Based Access**: Admin, Analyst, and Viewer roles

### Analytics

- **Dashboard**: Real-time statistics and emission breakdowns
- **Scope Visualization**: Pie and bar charts for Scope 1/2/3 emissions
- **Source Analytics**: Upload success rates and processing status
- **Export Ready**: Data structured for external reporting

## Architecture

### Backend

- **Framework**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL with JSON support
- **Authentication**: JWT tokens (djangorestframework-simplejwt)
- **File Processing**: Async threading with pandas for CSV parsing
- **API**: RESTful endpoints with pagination and filtering

### Frontend

- **Framework**: React 18 with Vite
- **State Management**: Zustand (auth) + TanStack Query (server state)
- **Styling**: Tailwind CSS
- **Charts**: Recharts for data visualization
- **Routing**: React Router v6

### Data Model

- **Company**: Multi-tenant organization container
- **User**: Role-based access control
- **DataSource**: Upload tracking and processing status
- **RawRecord**: Original uploaded data (immutable)
- **NormalizedEmissionRecord**: Processed emission records
- **AuditLog**: Complete change history
- **Notification**: User alerts for processing events

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

1. Create virtual environment:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Create superuser:

```bash
python manage.py createsuperuser
```

6. Load sample data (optional):

```bash
python manage.py shell
from core.models import Company, User
company = Company.objects.create(name="Demo Company")
User.objects.create_user(username="admin", password="admin123", email="admin@demo.com", company=company, role="admin")
User.objects.create_user(username="analyst", password="analyst123", email="analyst@demo.com", company=company, role="analyst")
```

7. Run development server:

```bash
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Configure environment:

```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8000/api" > .env
```

3. Run development server:

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Sample Data

Sample CSV files are provided in `backend/sample_data/`:

- `sap_fuel_data.csv` - SAP fuel and procurement data
- `utility_electricity_data.csv` - Utility electricity consumption
- `travel_data.csv` - Corporate travel bookings

Upload these through the UI to test the platform.

## Deployment

### Backend Deployment (Render/Railway/Fly.io)

1. Set environment variables:

```
SECRET_KEY=<generate-secure-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DB_NAME=<postgres-db-name>
DB_USER=<postgres-user>
DB_PASSWORD=<postgres-password>
DB_HOST=<postgres-host>
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

2. Deploy using platform CLI or connect GitHub repository

3. Run migrations:

```bash
python manage.py migrate
```

4. Create superuser:

```bash
python manage.py createsuperuser
```

### Frontend Deployment (Vercel/Netlify)

1. Set environment variable:

```
VITE_API_URL=https://your-backend-domain.com/api
```

2. Build command: `npm run build`

3. Output directory: `dist`

4. Deploy using platform CLI or connect GitHub repository

## API Overview

### Authentication

- `POST /api/auth/login/` - Login with username/password
- `POST /api/auth/register/` - Register new user
- `GET /api/auth/me/` - Get current user
- `POST /api/auth/refresh/` - Refresh JWT token

### Data Sources

- `GET /api/data-sources/` - List uploads
- `POST /api/data-sources/` - Upload new file
- `GET /api/data-sources/{id}/` - Get upload details

### Emission Records

- `GET /api/emission-records/` - List records (filterable)
- `GET /api/emission-records/{id}/` - Get record details
- `PATCH /api/emission-records/{id}/` - Update record
- `POST /api/emission-records/{id}/approve/` - Approve record
- `POST /api/emission-records/{id}/reject/` - Reject record
- `POST /api/emission-records/{id}/lock/` - Lock for audit
- `POST /api/emission-records/bulk_approve/` - Bulk approve

### Audit Logs

- `GET /api/audit-logs/` - List audit trail
- `GET /api/audit-logs/?record_id={id}` - Filter by record

### Dashboard

- `GET /api/dashboard/stats/` - Get dashboard statistics

## User Roles

### Admin

- Full system access
- Manage users and companies
- Lock records for audit
- Access all data across companies

### Analyst

- Upload and process data
- Review and approve/reject records
- Edit record details
- View audit logs
- Company-scoped access

### Viewer

- Read-only access
- View records and dashboards
- No approval or edit permissions
- Company-scoped access

## Testing

### Backend Tests

```bash
cd backend
python manage.py test
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## Project Structure

```
breathe-esg-platform/
├── backend/
│   ├── esg_platform/          # Django project settings
│   ├── core/                  # Main application
│   │   ├── models.py          # Database models
│   │   ├── serializers.py     # DRF serializers
│   │   ├── views.py           # API endpoints
│   │   ├── urls.py            # URL routing
│   │   ├── processors/        # Data processing logic
│   │   │   ├── sap_processor.py
│   │   │   ├── utility_processor.py
│   │   │   └── travel_processor.py
│   │   └── utils/             # Utility functions
│   │       ├── normalization.py
│   │       └── emission_factors.py
│   ├── sample_data/           # Sample CSV files
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── store/             # State management
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── MODEL.md                   # Data model documentation
├── DECISIONS.md               # Engineering decisions
├── TRADEOFFS.md               # What was not built
├── SOURCES.md                 # Data source research
└── README.md
```

## Key Design Decisions

1. **Async Processing**: Files are processed in background threads to avoid blocking uploads
2. **Raw Data Preservation**: Original data stored in JSON for audit and reprocessing
3. **Automatic Flagging**: Suspicious records flagged but not blocked (analyst review required)
4. **Audit Lock**: Approved records can be locked to prevent modifications
5. **Multi-Tenancy**: Company-level isolation for enterprise deployments

## Known Limitations

1. **Column Mapping**: Assumes English column names (German SAP exports require mapping)
2. **Distance Calculation**: Uses lookup table (production needs haversine formula)
3. **Emission Factors**: Hardcoded global averages (production needs regional factors)
4. **Duplicate Detection**: Not implemented (requires fuzzy matching)
5. **Real-Time Validation**: No pre-upload preview (validation happens post-upload)

See TRADEOFFS.md for detailed discussion of what was deliberately not built.

## Production Readiness

**Current State**: 70% production-ready

**To reach 90%**:

- Add flexible column mapping
- Implement distance calculation
- Support regional emission factors
- Add duplicate detection

**To reach 100%**:

- Direct API integrations (SAP OData, utility APIs, Concur API)
- ML-based anomaly detection
- Advanced approval workflows
- Email notifications

## License

Proprietary - Breathe ESG

## Contact

For questions or support, contact the development team.

---

**Built for Breathe ESG Tech Intern Assignment**
