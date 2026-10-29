from fastapi.testclient import TestClient
from backend.app.main import app
from sdk.client import DatasetClient, DatasetModel

def test_sdk_methods(monkeypatch):
    test_client = TestClient(app)
    client = DatasetClient(base_url="http://testserver")
    client.http = test_client # Mock http client with FastAPI TestClient

    # Test dataset creation via SDK
    ds = client.datasets.create(name="SDK Verification Dataset", domain="nlp", tags=["sdk", "nlp"])
    assert isinstance(ds, DatasetModel)
    assert ds.id.startswith("ds_")

    # Test list datasets
    all_ds = client.datasets.list()
    assert any(d.id == ds.id for d in all_ds)

    # Test provenance context manager
    with client.provenance.record(dataset_id=ds.id, operation="tokenization_stemming", parameters={"tokenizer": "bpe"}) as run:
        run.add_input("corpus_v1.txt")
        run.add_output("tokens_v1.parquet")

    lineage = client.provenance.get_lineage(ds.id)
    assert len(lineage["nodes"]) >= 1
    assert any(n["operation"] == "tokenization_stemming" for n in lineage["nodes"])
