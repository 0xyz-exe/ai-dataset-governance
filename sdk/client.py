import httpx
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

class DatasetModel:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.slug = data.get("slug", "")
        self.domain = data.get("domain", "")
        self.latest_version = data.get("latest_version")

    def __repr__(self):
        return f"<Dataset id={self.id} name='{self.name}' version={self.latest_version}>"

class ProvenanceRecorder:
    def __init__(self, client: "DatasetClient", dataset_id: str, operation: str, parameters: Optional[Dict[str, Any]] = None):
        self.client = client
        self.dataset_id = dataset_id
        self.operation = operation
        self.parameters = parameters or {}
        self.inputs: List[str] = []
        self.outputs: List[str] = []

    def add_input(self, artifact_name: str):
        self.inputs.append(artifact_name)

    def add_output(self, artifact_name: str):
        self.outputs.append(artifact_name)

    def finish(self):
        payload = {
            "dataset_id": self.dataset_id,
            "event_type": "transformation",
            "operation": self.operation,
            "parameters": {
                **self.parameters,
                "inputs": self.inputs,
                "outputs": self.outputs
            }
        }
        res = self.client.http.post(f"/api/v1/datasets/{self.dataset_id}/provenance/events", json=payload)
        res.raise_for_status()
        return res.json()

class ProvenanceNamespace:
    def __init__(self, client: "DatasetClient"):
        self.client = client

    @contextmanager
    def record(self, dataset_id: str, operation: str, parameters: Optional[Dict[str, Any]] = None):
        recorder = ProvenanceRecorder(self.client, dataset_id, operation, parameters)
        try:
            yield recorder
        finally:
            recorder.finish()

    def get_lineage(self, dataset_id: str):
        res = self.client.http.get(f"/api/v1/datasets/{dataset_id}/provenance/lineage")
        res.raise_for_status()
        return res.json()

class DatasetsNamespace:
    def __init__(self, client: "DatasetClient"):
        self.client = client

    def list(self, domain: Optional[str] = None, search: Optional[str] = None) -> List[DatasetModel]:
        params = {}
        if domain:
            params["domain"] = domain
        if search:
            params["search"] = search
        res = self.client.http.get("/api/v1/datasets", params=params)
        res.raise_for_status()
        return [DatasetModel(d) for d in res.json()]

    def get(self, dataset_id: str) -> DatasetModel:
        res = self.client.http.get(f"/api/v1/datasets/{dataset_id}")
        res.raise_for_status()
        return DatasetModel(res.json())

    def create(self, name: str, description: Optional[str] = None, domain: str = "tabular", tags: Optional[List[str]] = None) -> DatasetModel:
        payload = {"name": name, "description": description, "domain": domain, "tags": tags or []}
        res = self.client.http.post("/api/v1/datasets", json=payload)
        res.raise_for_status()
        return DatasetModel(res.json())

    def upload_file(self, dataset_id: str, file_path: str, logical_path: Optional[str] = None):
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"logical_path": logical_path} if logical_path else {}
            res = self.client.http.post(f"/api/v1/datasets/{dataset_id}/upload", files=files, data=data)
            res.raise_for_status()
            return res.json()

    def create_version(self, dataset_id: str, semver: str = "v1.0.0", description: str = "Release snapshot"):
        payload = {"semver": semver, "description": description}
        res = self.client.http.post(f"/api/v1/datasets/{dataset_id}/versions", json=payload)
        res.raise_for_status()
        return res.json()

    def run_quality(self, dataset_id: str, version_id: str):
        res = self.client.http.post(f"/api/v1/datasets/{dataset_id}/quality/run", params={"version_id": version_id})
        res.raise_for_status()
        return res.json()

class DatasetClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.http = httpx.Client(base_url=base_url, headers=headers, timeout=30.0)
        self.datasets = DatasetsNamespace(self)
        self.provenance = ProvenanceNamespace(self)
