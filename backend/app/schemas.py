from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "engineer"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: str

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    domain: Optional[str] = "tabular"
    task_type: Optional[str] = "classification"
    license: Optional[str] = "MIT"
    source_uri: Optional[str] = None
    visibility: Optional[str] = "public"

class DatasetCreate(DatasetBase):
    pass

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    domain: Optional[str] = None
    task_type: Optional[str] = None
    license: Optional[str] = None
    source_uri: Optional[str] = None
    visibility: Optional[str] = None
    status: Optional[str] = None

class FileItem(BaseModel):
    id: str
    logical_path: str
    blob_hash: str
    size_bytes: int
    created_at: str

class VersionCreate(BaseModel):
    semver: str = "v1.0.0"
    description: str = "Initial release"
    file_ids: Optional[List[str]] = None

class VersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_num: int
    semver: str
    description: Optional[str]
    creator_id: str
    parent_version_id: Optional[str]
    manifest_hash: str
    stats: Optional[Dict[str, Any]] = None
    schema_snapshot: Optional[Dict[str, Any]] = None
    quality_status: str
    created_at: str
    files: Optional[List[FileItem]] = []

class DatasetResponse(DatasetBase):
    id: str
    slug: str
    owner_id: str
    status: str
    created_at: str
    updated_at: str
    total_versions: int = 0
    total_files: int = 0
    total_size_bytes: int = 0
    latest_version: Optional[str] = None
    quality_status: str = "unverified"

class CompareResponse(BaseModel):
    base_version_id: str
    target_version_id: str
    base_semver: str
    target_semver: str
    added_files: List[Dict[str, Any]]
    removed_files: List[Dict[str, Any]]
    modified_files: List[Dict[str, Any]]
    unchanged_files: List[Dict[str, Any]]
    size_delta_bytes: int
    file_count_delta: int
    schema_changes: List[str]
    quality_delta: Dict[str, Any]

class QualityCheckResult(BaseModel):
    name: str
    dimension: str
    status: str # passed, failed, warning
    score: float
    message: str
    details: Optional[Dict[str, Any]] = None

class QualityRunResponse(BaseModel):
    id: str
    dataset_id: str
    version_id: str
    overall_score: float
    dimension_scores: Dict[str, float]
    status: str
    checks_passed: int
    checks_failed: int
    checks_warned: int
    checks: List[QualityCheckResult]
    created_at: str

class ProvenanceEventCreate(BaseModel):
    dataset_id: str
    version_id: Optional[str] = None
    event_type: str
    operation: str
    parameters: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = "dataset-governance-sdk"
    tool_version: Optional[str] = "1.0.0"
    source_uri: Optional[str] = None
    parent_event_ids: Optional[List[str]] = []

class SchemaCreate(BaseModel):
    name: str
    format_type: str # csv, json, parquet, yolo, coco
    schema_def: Dict[str, Any]

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_id: str
    version_id: str
    model_name: str
    model_version: Optional[str] = "1.0.0"
    framework: Optional[str] = "PyTorch"
    hyperparameters: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    git_commit: Optional[str] = None

class AuditLogItem(BaseModel):
    id: str
    actor: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: str
