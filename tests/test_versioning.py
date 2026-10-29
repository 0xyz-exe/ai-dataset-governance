import pytest
from backend.app.db import init_db
from backend.app.storage import storage
from backend.app.services.dataset_service import DatasetService
from backend.app.services.version_service import VersionService
from backend.app.services.compare_service import CompareService
from backend.app.schemas import DatasetCreate, VersionCreate

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_dataset_and_version_lifecycle():
    # 1. Create dataset
    ds = DatasetService.create_dataset(DatasetCreate(name="Autonomous Vehicle Sensors", domain="vision"))
    assert ds["id"].startswith("ds_")

    # 2. Upload file
    content1 = b"timestamp,lidar_range,camera_status\n1001,23.5,active\n1002,24.1,active\n"
    h1, s1 = storage.store_bytes(content1)
    f1 = DatasetService.add_file(ds["id"], "sensors/telemetry.csv", h1, s1)
    assert f1["blob_hash"] == h1

    # 3. Create version v1.0.0
    v1 = VersionService.create_version(ds["id"], VersionCreate(semver="v1.0.0", description="Initial sensor snapshot"))
    assert v1["semver"] == "v1.0.0"
    assert v1["version_num"] == 1
    assert len(v1["files"]) == 1
    assert v1["files"][0]["logical_path"] == "sensors/telemetry.csv"

    # 4. Ingest new file for v1.1.0
    content2 = b"timestamp,lidar_range,camera_status\n1003,22.8,active\n"
    h2, s2 = storage.store_bytes(content2)
    DatasetService.add_file(ds["id"], "sensors/telemetry_batch2.csv", h2, s2)

    v2 = VersionService.create_version(ds["id"], VersionCreate(semver="v1.1.0", description="Second batch"))
    assert v2["version_num"] == 2
    assert len(v2["files"]) == 2 # Contains inherited file + newly added file

    # 5. Compare versions
    diff = CompareService.compare_versions(v1["id"], v2["id"])
    assert diff["base_semver"] == "v1.0.0"
    assert diff["target_semver"] == "v1.1.0"
    assert len(diff["added_files"]) == 1
    assert len(diff["unchanged_files"]) == 1
    assert len(diff["removed_files"]) == 0
