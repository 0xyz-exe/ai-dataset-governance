from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import init_db

init_db()
client = TestClient(app)

def test_api_overview_and_lifecycle():
    # 1. Overview stats
    res = client.get("/api/v1/overview/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_datasets" in stats

    # 2. Create dataset
    ds_payload = {
        "name": "E-Commerce Fraud Detection",
        "description": "Tabular credit transaction sequences",
        "domain": "tabular",
        "task_type": "anomaly-detection",
        "tags": ["fraud", "finance", "transactions"],
        "license": "Apache-2.0"
    }
    create_res = client.post("/api/v1/datasets", json=ds_payload)
    assert create_res.status_code == 200
    ds = create_res.json()
    dataset_id = ds["id"]

    # 3. Upload sample file
    csv_data = b"trans_id,amount,is_fraud\nt_101,45.50,0\nt_102,12000.00,1\n"
    files = {"file": ("transactions.csv", csv_data, "text/csv")}
    up_res = client.post(f"/api/v1/datasets/{dataset_id}/upload", files=files)
    assert up_res.status_code == 200

    # 4. Create version
    v_res = client.post(f"/api/v1/datasets/{dataset_id}/versions", json={"semver": "v1.0.0", "description": "Release v1"})
    assert v_res.status_code == 200
    v = v_res.json()
    version_id = v["id"]

    # 5. Run quality checks
    q_res = client.post(f"/api/v1/datasets/{dataset_id}/quality/run?version_id={version_id}")
    assert q_res.status_code == 200
    q = q_res.json()
    assert q["overall_score"] > 0

    # 6. Check license
    lic_res = client.get("/api/v1/governance/license-check?license=Apache-2.0")
    assert lic_res.status_code == 200
    assert lic_res.json()["status"] == "approved"
