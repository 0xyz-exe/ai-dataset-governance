import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional, Dict, Any

from backend.app.schemas import (
    DatasetCreate, DatasetUpdate, VersionCreate,
    ProvenanceEventCreate, SchemaCreate, ExperimentCreate
)
from backend.app.storage import storage
from backend.app.services.dataset_service import DatasetService
from backend.app.services.version_service import VersionService
from backend.app.services.compare_service import CompareService
from backend.app.services.quality_service import QualityService
from backend.app.services.provenance_service import ProvenanceService
from backend.app.services.schema_service import SchemaService
from backend.app.services.experiment_service import ExperimentService
from backend.app.services.governance_service import GovernanceService
from backend.app.db import db_session

api_router = APIRouter(prefix="/api/v1")

# --- Overview & Telemetry ---
@api_router.get("/overview/stats")
def get_system_stats():
    with db_session() as conn:
        ds_cnt = conn.execute("SELECT count(*) as c FROM datasets").fetchone()["c"]
        ver_cnt = conn.execute("SELECT count(*) as c FROM dataset_versions").fetchone()["c"]
        blob_row = conn.execute("SELECT count(*) as c, coalesce(sum(size_bytes), 0) as s FROM dataset_blobs").fetchone()
        qr_row = conn.execute("SELECT count(*) as c, coalesce(avg(overall_score), 0) as avg_sc FROM quality_runs").fetchone()
        exp_cnt = conn.execute("SELECT count(*) as c FROM experiments").fetchone()["c"]
        audit_cnt = conn.execute("SELECT count(*) as c FROM audit_logs").fetchone()["c"]

        # Quality distribution
        pass_cnt = conn.execute("SELECT count(*) as c FROM dataset_versions WHERE quality_status = 'passed'").fetchone()["c"]
        warn_cnt = conn.execute("SELECT count(*) as c FROM dataset_versions WHERE quality_status = 'warning'").fetchone()["c"]
        fail_cnt = conn.execute("SELECT count(*) as c FROM dataset_versions WHERE quality_status = 'failed'").fetchone()["c"]
        unv_cnt = conn.execute("SELECT count(*) as c FROM dataset_versions WHERE quality_status = 'unverified'").fetchone()["c"]

    return {
        "total_datasets": ds_cnt,
        "total_versions": ver_cnt,
        "total_blobs": blob_row["c"],
        "total_storage_bytes": blob_row["s"],
        "total_quality_runs": qr_row["c"],
        "avg_quality_score": round(qr_row["avg_sc"], 1),
        "total_experiments": exp_cnt,
        "total_audit_events": audit_cnt,
        "quality_distribution": {
            "passed": pass_cnt,
            "warning": warn_cnt,
            "failed": fail_cnt,
            "unverified": unv_cnt
        }
    }

# --- Datasets ---
@api_router.get("/datasets")
def list_datasets(domain: Optional[str] = None, search: Optional[str] = None):
    return DatasetService.list_datasets(domain=domain, search=search)

@api_router.post("/datasets")
def create_dataset(data: DatasetCreate):
    res = DatasetService.create_dataset(data)
    GovernanceService.log_audit("admin", "create_dataset", "dataset", res["id"], {"name": data.name})
    return res

@api_router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    res = DatasetService.get_dataset(dataset_id)
    if not res:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return res

@api_router.post("/datasets/{dataset_id}/upload")
async def upload_file(
    dataset_id: str,
    file: UploadFile = File(...),
    logical_path: Optional[str] = Form(None)
):
    ds = DatasetService.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    target_path = logical_path or file.filename or "unnamed_file"
    # Defend against path traversal
    clean_path = target_path.replace("\\", "/").strip("/").replace("..", "_")

    digest, size_bytes = storage.store_stream(file.file)
    f_record = DatasetService.add_file(dataset_id, clean_path, digest, size_bytes)

    # Record provenance ingestion event
    ProvenanceService.record_event(
        ProvenanceEventCreate(
            dataset_id=dataset_id,
            event_type="file_ingested",
            operation="upload_file",
            parameters={"logical_path": clean_path, "sha256": digest, "size": size_bytes}
        )
    )

    GovernanceService.log_audit("admin", "upload_file", "dataset_file", f_record["id"], {"path": clean_path, "sha256": digest})
    return f_record

@api_router.get("/datasets/{dataset_id}/files")
def list_files(dataset_id: str, version_id: Optional[str] = None):
    return DatasetService.list_files(dataset_id, version_id=version_id)

# --- Versions ---
@api_router.post("/datasets/{dataset_id}/versions")
def create_version(dataset_id: str, data: VersionCreate):
    try:
        v = VersionService.create_version(dataset_id, data)
        GovernanceService.log_audit("admin", "create_version", "dataset_version", v["id"], {"semver": data.semver})
        return v
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/datasets/{dataset_id}/versions")
def list_versions(dataset_id: str):
    return VersionService.list_versions(dataset_id)

@api_router.get("/datasets/{dataset_id}/versions/{version_id}")
def get_version(dataset_id: str, version_id: str):
    v = VersionService.get_version(version_id)
    if not v or v.get("dataset_id") != dataset_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return v

@api_router.post("/datasets/{dataset_id}/versions/{version_id}/restore")
def restore_version(dataset_id: str, version_id: str):
    try:
        restored = VersionService.restore_version(dataset_id, version_id)
        GovernanceService.log_audit("admin", "restore_version", "dataset_version", restored["id"], {"restored_from": version_id})
        return restored
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Compare ---
@api_router.get("/datasets/{dataset_id}/compare")
def compare_versions(dataset_id: str, base_version_id: str = Query(...), target_version_id: str = Query(...)):
    try:
        return CompareService.compare_versions(base_version_id, target_version_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Quality ---
@api_router.post("/datasets/{dataset_id}/quality/run")
def run_quality_checks(dataset_id: str, version_id: str = Query(...)):
    try:
        res = QualityService.run_checks(dataset_id, version_id)
        GovernanceService.log_audit("admin", "run_quality_checks", "quality_run", res["id"], {"score": res["overall_score"]})
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/datasets/{dataset_id}/quality/runs")
def list_quality_runs(dataset_id: str, version_id: Optional[str] = None):
    return QualityService.list_runs(dataset_id, version_id=version_id)

# --- Provenance ---
@api_router.post("/datasets/{dataset_id}/provenance/events")
def record_provenance_event(dataset_id: str, data: ProvenanceEventCreate):
    data.dataset_id = dataset_id
    return ProvenanceService.record_event(data)

@api_router.get("/datasets/{dataset_id}/provenance/lineage")
def get_provenance_lineage(dataset_id: str):
    return ProvenanceService.get_lineage(dataset_id)

# --- Schemas ---
@api_router.post("/datasets/{dataset_id}/schemas")
def register_schema(dataset_id: str, data: SchemaCreate):
    return SchemaService.register_schema(dataset_id, data)

@api_router.get("/datasets/{dataset_id}/schemas")
def list_schemas(dataset_id: str):
    return SchemaService.list_schemas(dataset_id)

@api_router.post("/schemas/infer")
def infer_schema(content: str = Form(...), name: str = Form("inferred_csv_schema")):
    return SchemaService.infer_schema_from_csv(content, name=name)

# --- Experiments ---
@api_router.post("/experiments")
def register_experiment(data: ExperimentCreate):
    res = ExperimentService.register_experiment(data)
    GovernanceService.log_audit("admin", "register_experiment", "experiment", res["id"], {"model": data.model_name})
    return res

@api_router.get("/experiments")
def list_experiments(dataset_id: Optional[str] = None, version_id: Optional[str] = None):
    return ExperimentService.list_experiments(dataset_id=dataset_id, version_id=version_id)

# --- Governance & Audit ---
@api_router.get("/governance/license-check")
def check_license(license: str = Query(...)):
    return GovernanceService.check_license_compliance(license)

@api_router.get("/governance/audit-logs")
def list_audit_logs(limit: int = 100):
    return GovernanceService.list_audit_logs(limit=limit)
