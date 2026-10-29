from backend.app.db import init_db
from backend.app.storage import storage
from backend.app.services.dataset_service import DatasetService
from backend.app.services.version_service import VersionService
from backend.app.services.quality_service import QualityService
from backend.app.services.provenance_service import ProvenanceService
from backend.app.services.schema_service import SchemaService
from backend.app.services.experiment_service import ExperimentService
from backend.app.schemas import (
    DatasetCreate, VersionCreate, ProvenanceEventCreate,
    SchemaCreate, ExperimentCreate
)

def seed():
    init_db()

    # 1. Dataset: Autonomous Vision
    ds1 = DatasetService.create_dataset(DatasetCreate(
        name="Nighttime Urban Traffic Vision",
        description="Low-light automotive computer vision dataset with 2D bounding box annotations (YOLO/COCO formats).",
        domain="vision",
        task_type="object-detection",
        tags=["automotive", "yolo", "coco", "night-vision", "adas"],
        license="Apache-2.0",
        source_uri="https://datasets.internal.ai/traffic-nighttime",
        visibility="public"
    ))

    # Add files for ds1
    yolo_labels = b"0 0.45 0.52 0.12 0.22\n1 0.72 0.35 0.08 0.15\n0 0.21 0.60 0.14 0.28\n"
    h_yolo, s_yolo = storage.store_bytes(yolo_labels)
    DatasetService.add_file(ds1["id"], "labels/frame_0001.txt", h_yolo, s_yolo)

    classes_txt = b"pedestrian\nvehicle\ncyclist\ntraffic_light\n"
    h_cls, s_cls = storage.store_bytes(classes_txt)
    DatasetService.add_file(ds1["id"], "classes.txt", h_cls, s_cls)

    # Version v1.0.0
    v1_ds1 = VersionService.create_version(ds1["id"], VersionCreate(
        semver="v1.0.0",
        description="Raw ingested nighttime sensor frames with initial human annotator tags"
    ))

    # Run quality check
    QualityService.run_checks(ds1["id"], v1_ds1["id"])

    # Provenance
    p1 = ProvenanceService.record_event(ProvenanceEventCreate(
        dataset_id=ds1["id"],
        version_id=v1_ds1["id"],
        event_type="ingestion",
        operation="lidar_camera_sync",
        parameters={"fps": 30, "exposure_ms": 12.5, "sensor": "Sony IMX490"}
    ))

    p2 = ProvenanceService.record_event(ProvenanceEventCreate(
        dataset_id=ds1["id"],
        version_id=v1_ds1["id"],
        event_type="transformation",
        operation="clahe_preprocessing",
        parameters={"clip_limit": 2.0, "tile_grid_size": [8, 8]},
        parent_event_ids=[p1["id"]]
    ))

    # Version v1.1.0 with CLAHE augmented data
    yolo_enhanced = b"0 0.45 0.52 0.12 0.22\n1 0.72 0.35 0.08 0.15\n0 0.21 0.60 0.14 0.28\n2 0.88 0.45 0.05 0.10\n"
    h_enh, s_enh = storage.store_bytes(yolo_enhanced)
    DatasetService.add_file(ds1["id"], "labels/frame_0002.txt", h_enh, s_enh)

    v2_ds1 = VersionService.create_version(ds1["id"], VersionCreate(
        semver="v1.1.0",
        description="CLAHE contrast enhancement & expanded cyclist bounding boxes"
    ))
    QualityService.run_checks(ds1["id"], v2_ds1["id"])

    # Experiment linking v2_ds1
    ExperimentService.register_experiment(ExperimentCreate(
        name="YOLOv11-Night-Baseline",
        description="Ultralytics YOLOv11 small architecture trained on CLAHE enhanced v1.1.0 dataset",
        dataset_id=ds1["id"],
        version_id=v2_ds1["id"],
        model_name="yolov11s-night-detector",
        model_version="1.0.0",
        framework="PyTorch",
        hyperparameters={"epochs": 100, "batch_size": 32, "lr0": 0.01, "imgsz": 640},
        metrics={"mAP50": 0.874, "mAP50-95": 0.642, "precision": 0.891, "recall": 0.835},
        git_commit="9f8a3c2"
    ))

    # 2. Dataset: Financial Fraud
    ds2 = DatasetService.create_dataset(DatasetCreate(
        name="Card Transactions & Fraud Signals",
        description="High-throughput transaction tabular dataset with class imbalance and PCA feature transforms.",
        domain="tabular",
        task_type="fraud-detection",
        tags=["fintech", "fraud", "tabular", "transactions", "pci-dss"],
        license="MIT",
        visibility="public"
    ))

    csv_data = (
        "transaction_id,timestamp,user_id,amount_usd,merchant_cat,is_fraud,risk_score\n"
        "tx_1001,1730160000,usr_881,14.50,dining,0,0.02\n"
        "tx_1002,1730160030,usr_420,1280.00,electronics,1,0.94\n"
        "tx_1003,1730160060,usr_119,3.25,transit,0,0.01\n"
        "tx_1004,1730160090,usr_902,590.20,jewelry,1,0.89\n"
        "tx_1005,1730160120,usr_331,45.00,grocery,0,0.05\n"
    ).encode("utf-8")
    h_csv, s_csv = storage.store_bytes(csv_data)
    DatasetService.add_file(ds2["id"], "data/transactions_sample.csv", h_csv, s_csv)

    v1_ds2 = VersionService.create_version(ds2["id"], VersionCreate(
        semver="v1.0.0",
        description="Standard benchmark transactions baseline with 5 verified fraud cases"
    ))
    QualityService.run_checks(ds2["id"], v1_ds2["id"])

    # Register schema for ds2
    SchemaService.register_schema(ds2["id"], SchemaCreate(
        name="TransactionRowSchema",
        format_type="csv",
        schema_def={
            "fields": [
                {"name": "transaction_id", "type": "string", "required": True},
                {"name": "timestamp", "type": "integer", "required": True},
                {"name": "user_id", "type": "string", "required": True},
                {"name": "amount_usd", "type": "float", "required": True},
                {"name": "merchant_cat", "type": "string", "required": False},
                {"name": "is_fraud", "type": "integer", "required": True},
                {"name": "risk_score", "type": "float", "required": False}
            ]
        }
    ))

    print("Seed completed successfully.")

if __name__ == "__main__":
    seed()
