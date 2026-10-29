import pytest
from backend.app.db import init_db
from backend.app.storage import storage
from backend.app.services.dataset_service import DatasetService
from backend.app.services.version_service import VersionService
from backend.app.services.quality_service import QualityService
from backend.app.schemas import DatasetCreate, VersionCreate

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_quality_checks_tabular_and_yolo():
    ds = DatasetService.create_dataset(DatasetCreate(name="Traffic Camera Dataset", domain="vision"))

    # Add CSV with null values
    csv_bytes = b"id,vehicle_type,speed\n1,car,45.2\n2,truck,\n3,car,55.0\n4,bike,\n"
    h1, s1 = storage.store_bytes(csv_bytes)
    DatasetService.add_file(ds["id"], "metadata/speed.csv", h1, s1)

    # Add valid YOLO label file
    yolo_bytes = b"0 0.5 0.5 0.2 0.3\n1 0.7 0.8 0.1 0.2\n"
    h2, s2 = storage.store_bytes(yolo_bytes)
    DatasetService.add_file(ds["id"], "labels/frame_001.txt", h2, s2)

    v1 = VersionService.create_version(ds["id"], VersionCreate(semver="v1.0.0", description="Quality check candidate"))

    report = QualityService.run_checks(ds["id"], v1["id"])
    assert report["overall_score"] > 50.0
    assert "integrity" in report["dimension_scores"]
    assert report["dimension_scores"]["integrity"] == 100.0
    assert report["checks_passed"] > 0
