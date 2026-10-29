# System Architecture

## Overview

AI Dataset Governance is designed with a local-first, modular architecture that ensures full provenance, deterministic version manifests, and strict quality gates for AI and ML datasets.

```mermaid
graph TD
    User([Engineer / Researcher]) --> UI[React Web Interface]
    User --> CLI[CLI / Python SDK]
    UI --> API[FastAPI REST API /api/v1]
    CLI --> API

    subgraph Core Engine
        API --> Reg[Dataset Registry]
        API --> Ver[Versioning Engine]
        API --> Qual[Quality & Validation Engine]
        API --> Prov[Provenance & DAG Engine]
        API --> Sch[Schema Registry]
        API --> Exp[ML Experiment Tracker]
        API --> Gov[Governance & Audit Trail]
    end

    subgraph Storage & Persistence
        Ver --> CAS[Content-Addressed Blob Storage]
        Reg --> DB[(SQLite / PostgreSQL)]
        Prov --> DB
        Gov --> DB
    end
```

## Storage Engine (CAS)

The storage subsystem uses Content-Addressed Storage (CAS) where files are stored under `/data/storage/blobs/xx/<sha256_hash>`.
Identical payload bytes across different versions, filenames, or datasets are automatically deduplicated.
