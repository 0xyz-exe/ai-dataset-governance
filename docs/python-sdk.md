# Python SDK

The `sdk` module provides an idiomatic client for data scientists and MLOps engineers.

## Example Usage

```python
from sdk.client import DatasetClient

# Initialize client
client = DatasetClient(base_url="http://localhost:8000")

# Fetch dataset
dataset = client.datasets.get("ds_8195414f67e0")
print(f"Dataset: {dataset.name}, latest version: {dataset.latest_version}")

# Record pipeline transformation provenance
with client.provenance.record(
    dataset_id=dataset.id,
    operation="clahe_preprocessing",
    parameters={
        "clip_limit": 2.0,
        "tile_grid_size": [8, 8]
    }
) as run:
    run.add_input("raw_dataset_v1")
    run.add_output("clahe_dataset_v1")

# Commit a new version snapshot
version = client.datasets.create_version(
    dataset_id=dataset.id,
    semver="v1.1.0",
    description="CLAHE augmented images"
)

# Run automated quality checks
quality = client.datasets.run_quality(
    dataset_id=dataset.id,
    version_id=version["id"]
)
print(f"Quality score: {quality['overall_score']}% ({quality['status']})")
```
