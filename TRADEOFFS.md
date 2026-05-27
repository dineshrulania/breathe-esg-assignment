# Tradeoffs: What Was Deliberately Not Built

## 1. Real-Time Data Validation & Preview

### What It Would Be

Before processing an uploaded file, show the user:

- First 10 rows of parsed data
- Detected column mappings
- Validation errors and warnings
- Estimated processing time
- Option to adjust mappings or cancel

### Why It Wasn't Built

**Time Constraint**: Implementing a robust preview system requires:

- Streaming CSV parsing (don't load entire file)
- Frontend table component with column mapping UI
- Backend endpoint for partial file analysis
- State management for mapping adjustments

**Complexity**: Column mapping is non-trivial:

- SAP exports have German/English column name variations
- Utility CSVs have inconsistent headers across providers
- Heuristic matching (fuzzy string matching) is error-prone
- Manual mapping UI adds significant UX complexity

**Current Workaround**:

- Users see processing results after upload completes
- Failed rows are logged with error messages
- Users can re-upload with corrections

**When to Build It**:

- After onboarding 5+ clients with diverse formats
- When upload failure rate exceeds 20%
- When PM feedback indicates mapping is a major pain point

**Implementation Estimate**: 3-4 days

- Backend: Streaming parser, column detection, mapping API
- Frontend: Interactive table, mapping controls, validation display

---

## 2. Advanced Anomaly Detection & Data Quality Scoring

### What It Would Be

Machine learning-based anomaly detection:

- Train models on historical data per company
- Detect statistical outliers (z-score, isolation forest)
- Identify duplicate records across sources
- Flag temporal anomalies (sudden spikes, missing periods)
- Assign data quality scores (0-100) to each record
- Suggest corrections based on historical patterns

### Why It Wasn't Built

**Data Requirements**: ML models need:

- Sufficient historical data (6+ months per company)
- Labeled training data (confirmed anomalies)
- Per-company model training (not one-size-fits-all)

**Complexity**: Production ML requires:

- Model training pipeline
- Feature engineering (temporal, categorical, numerical)
- Model versioning and A/B testing
- Explainability (why was this flagged?)
- Continuous retraining as data evolves

**Current Workaround**:

- Simple rule-based heuristics (negative values, future dates, extreme values)
- Analysts use domain knowledge to spot issues
- Suspicious flag is binary (yes/no), not scored

**When to Build It**:

- After accumulating 6+ months of data per client
- When analyst review time becomes a bottleneck
- When false positive rate of rule-based flagging is too high
- When clients request automated data quality reports

**Implementation Estimate**: 2-3 weeks

- Data pipeline: Feature extraction, training data labeling
- Model: Isolation forest or autoencoder for anomaly detection
- API: Scoring endpoint, explainability
- Frontend: Quality score visualization, drill-down

**Alternative Approach**: Partner with existing data quality platforms (Great Expectations, Monte Carlo) rather than building in-house.

---

## 3. Granular Permissions & Approval Workflows

### What It Would Be

Enterprise-grade permission system:

- Custom roles beyond Admin/Analyst/Viewer
- Permission matrix (who can approve, edit, lock, export)
- Multi-stage approval workflows (analyst → manager → auditor)
- Delegation (assign records to specific analysts)
- Approval limits (analyst can approve up to $X emissions)
- Regional restrictions (EU analyst can't see US data)
- Audit separation of duties (uploader ≠ approver)

### Why It Wasn't Built

**Complexity**: Granular permissions require:

- Permission model (roles, permissions, assignments)
- Workflow engine (state machine for multi-stage approvals)
- UI for permission management
- Extensive testing (permission bugs are security issues)

**Unclear Requirements**: Without real client feedback:

- Don't know which permissions are actually needed
- Risk over-engineering a system that's too complex
- Different clients may have incompatible workflow requirements

**Current Workaround**:

- Three fixed roles cover 80% of use cases
- Admins have full control
- Analysts can approve/reject but not lock
- Viewers are read-only

**When to Build It**:

- After onboarding 3+ enterprise clients
- When clients explicitly request custom workflows
- When audit requirements mandate separation of duties
- When regional data restrictions are required (GDPR, data residency)

**Implementation Estimate**: 1-2 weeks

- Backend: Permission model, workflow engine, authorization checks
- Frontend: Permission management UI, workflow visualization
- Testing: Comprehensive permission matrix testing

**Alternative Approach**: Integrate with enterprise IAM (Okta, Auth0) for role management rather than building custom.

---

## Why These Three?

These represent the three most common "next features" clients request:

1. **Data Validation Preview**: Reduces upload friction and errors
2. **Advanced Anomaly Detection**: Scales analyst productivity
3. **Granular Permissions**: Meets enterprise compliance requirements

Each was deliberately scoped out to:

- Ship a working MVP in 4 days
- Validate core workflows before adding complexity
- Avoid premature optimization
- Gather real user feedback before building

## Other Notable Omissions

**Not Built, But Important**:

- **CSV Export**: Analysts need to export reviewed data for reporting
- **Bulk Edit**: Analysts need to update multiple records at once
- **Email Notifications**: Async processing needs email alerts
- **API Documentation**: Swagger/OpenAPI for external integrations
- **Mobile Responsive**: Current UI is desktop-optimized
- **Dark Mode**: Nice-to-have for analyst UX
- **Keyboard Shortcuts**: Power users want keyboard navigation
- **Undo/Redo**: Analysts need to revert changes
- **Comments/Discussion**: Analysts need to discuss flagged records
- **File Templates**: Provide downloadable CSV templates for each source

**Not Built, Less Critical**:

- **Multi-language Support**: i18n for global clients
- **Custom Dashboards**: Drag-and-drop dashboard builder
- **Scheduled Imports**: Cron-based recurring uploads
- **Webhooks**: External system notifications
- **GraphQL API**: Alternative to REST
- **Real-time Collaboration**: Multiple analysts reviewing simultaneously
- **Version Control**: Git-like versioning for records
- **Data Lineage Visualization**: Graph view of data transformations

## Decision Framework

When deciding what not to build, I asked:

1. **Is it required for core workflow?** (upload → normalize → review → approve)
2. **Can it be added later without major refactoring?**
3. **Do we have enough information to build it correctly?**
4. **What's the cost of getting it wrong?**

Features that failed any of these tests were deferred.
