# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-10-29

### Added
- Core Dataset Registry supporting Tabular, Vision, and NLP domains.
- Content-addressed blob storage engine using SHA-256 digests and deduplication.
- Immutable Dataset Versioning Engine with reproducible manifests and restore workflow.
- Differential Version Comparison (added, removed, modified files, byte deltas, schema diffs).
- Multi-dimensional Data Quality Engine:
  - Tabular null checks, duplicate row detection, category validations.
  - Computer Vision integrity verification via Pillow.
  - YOLO bounding box normalization [0, 1] validation.
  - COCO JSON structure, categories, and annotation checking.
- Provenance & Data Lineage Graph (DAG) with cycle rejection and actor tracking.
- Schema Registry with breaking change detection (column drops, type mismatches, nullability tightening).
- Lightweight ML Experiment Tracking linking models, metrics, and commits to immutable dataset versions.
- Governance policies, license compliance categorization, and append-only audit trail logging.
- Python SDK (`DatasetClient`, `ProvenanceRecorder`) and CLI (`dataset-governance`).
- Modern React + Tailwind CSS dashboard with dark theme and interactive explorer.
