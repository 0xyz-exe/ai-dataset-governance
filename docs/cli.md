# Command Line Interface (CLI)

The `dataset-governance` CLI provides scriptable terminal operations for CI/CD pipelines and local data workflows.

## Commands

```bash
# Initialize storage and database
python -m cli.main init

# List datasets
python -m cli.main dataset list

# Create a new dataset
python -m cli.main dataset create --name "Autonomous Vision" --domain vision --desc "LIDAR & Camera"

# Ingest file
python -m cli.main dataset upload --dataset-id ds_xxx --file ./data/sample.csv --logical-path telemetry.csv

# Commit version snapshot
python -m cli.main version create --dataset-id ds_xxx --semver v1.0.0 --desc "Initial release"

# Compare two versions
python -m cli.main version compare --base ver_111 --target ver_222

# Run quality checks
python -m cli.main quality run --dataset-id ds_xxx --version-id ver_xxx

# Verify cryptographic manifest integrity
python -m cli.main manifest verify --version-id ver_xxx

# Inspect lineage DAG
python -m cli.main provenance inspect --dataset-id ds_xxx
```
