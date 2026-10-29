import pytest
from backend.app.db import init_db
from backend.app.services.dataset_service import DatasetService
from backend.app.services.provenance_service import ProvenanceService
from backend.app.services.schema_service import SchemaService
from backend.app.schemas import DatasetCreate, ProvenanceEventCreate, SchemaCreate

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_provenance_dag_lineage():
    ds = DatasetService.create_dataset(DatasetCreate(name="Genomics Pipeline Data", domain="tabular"))

    # Event 1: Ingestion
    e1 = ProvenanceService.record_event(ProvenanceEventCreate(
        dataset_id=ds["id"],
        event_type="ingestion",
        operation="fetch_public_genbank",
        parameters={"source": "ncbi"}
    ))

    # Event 2: CLAHE / Preprocessing with parent e1
    e2 = ProvenanceService.record_event(ProvenanceEventCreate(
        dataset_id=ds["id"],
        event_type="transformation",
        operation="sequence_cleaning",
        parameters={"filter_ambiguous": True},
        parent_event_ids=[e1["id"]]
    ))

    lineage = ProvenanceService.get_lineage(ds["id"])
    assert len(lineage["nodes"]) == 2
    assert len(lineage["edges"]) == 1
    assert lineage["edges"][0]["source"] == e1["id"]
    assert lineage["edges"][0]["target"] == e2["id"]

def test_schema_breaking_changes():
    old_schema = {
        "fields": [
            {"name": "user_id", "type": "integer", "required": True},
            {"name": "email", "type": "string", "nullable": True}
        ]
    }
    new_schema = {
        "fields": [
            # user_id removed -> breaking
            # email nullable -> required -> breaking
            {"name": "email", "type": "string", "nullable": False}
        ]
    }

    breaking = SchemaService.detect_breaking_changes(old_schema, new_schema)
    assert len(breaking) == 2
    assert any("user_id" in b for b in breaking)
    assert any("email" in b for b in breaking)
