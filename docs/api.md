# REST API Specification

The API is mounted under `/api/v1`.

## Endpoints

### System & Telemetry
- `GET /api/v1/overview/stats`: Returns system telemetry, totals, and quality distributions.

### Datasets
- `GET /api/v1/datasets`: List datasets with optional `domain` and `search` query parameters.
- `POST /api/v1/datasets`: Register a new dataset.
- `GET /api/v1/datasets/{dataset_id}`: Retrieve dataset metadata and statistics.
- `POST /api/v1/datasets/{dataset_id}/upload`: Upload and ingest file payload.
- `GET /api/v1/datasets/{dataset_id}/files`: List all files registered under dataset.

### Versioning
- `POST /api/v1/datasets/{dataset_id}/versions`: Commit an immutable snapshot.
- `GET /api/v1/datasets/{dataset_id}/versions`: List version history.
- `GET /api/v1/datasets/{dataset_id}/versions/{version_id}`: Get version details and manifest.
- `POST /api/v1/datasets/{dataset_id}/versions/{version_id}/restore`: Restore an earlier version snapshot.
- `GET /api/v1/datasets/{dataset_id}/compare?base_version_id={id}&target_version_id={id}`: Differential comparison.

### Quality Assurance & Gates
- `POST /api/v1/datasets/{dataset_id}/quality/run?version_id={id}`: Execute automated validation suite.
- `GET /api/v1/datasets/{dataset_id}/quality/runs`: Fetch historical quality runs.

### Provenance & Lineage
- `POST /api/v1/datasets/{dataset_id}/provenance/events`: Record a pipeline transformation event.
- `GET /api/v1/datasets/{dataset_id}/provenance/lineage`: Fetch DAG representation.

### Schemas
- `POST /api/v1/datasets/{dataset_id}/schemas`: Register a dataset schema.
- `GET /api/v1/datasets/{dataset_id}/schemas`: List registered schemas.
- `POST /api/v1/schemas/infer`: Infer schema fields and types from CSV text.

### Experiments & Governance
- `POST /api/v1/experiments`: Register an ML training run linked to a dataset version.
- `GET /api/v1/experiments`: List experiments.
- `GET /api/v1/governance/license-check`: Inspect license compliance and commercial usability.
- `GET /api/v1/governance/audit-logs`: List append-only audit trail.
