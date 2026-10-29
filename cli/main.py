import sys
import json
import argparse
from pathlib import Path
from backend.app.storage import storage
from backend.app.services.dataset_service import DatasetService
from backend.app.services.version_service import VersionService
from backend.app.services.compare_service import CompareService
from backend.app.services.quality_service import QualityService
from backend.app.services.provenance_service import ProvenanceService
from backend.app.schemas import DatasetCreate, VersionCreate, ProvenanceEventCreate
from backend.app.db import init_db

def main():
    init_db()
    parser = argparse.ArgumentParser(
        prog="dataset-governance",
        description="AI Dataset Governance CLI — Versioning, Provenance & Quality Management"
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize local storage & SQLite database")

    # dataset
    ds_parser = subparsers.add_parser("dataset", help="Manage datasets")
    ds_sub = ds_parser.add_subparsers(dest="subcommand")

    ds_list = ds_sub.add_parser("list", help="List registered datasets")
    ds_create = ds_sub.add_parser("create", help="Register a new dataset")
    ds_create.add_argument("--name", required=True, help="Dataset name")
    ds_create.add_argument("--domain", default="tabular", help="Domain: tabular, vision, nlp")
    ds_create.add_argument("--desc", default="", help="Description")

    ds_upload = ds_sub.add_parser("upload", help="Ingest a file into dataset")
    ds_upload.add_argument("--dataset-id", required=True, help="Target dataset ID")
    ds_upload.add_argument("--file", required=True, help="Path to local file")
    ds_upload.add_argument("--logical-path", help="Logical filename or relative path")

    # version
    ver_parser = subparsers.add_parser("version", help="Manage dataset versions")
    ver_sub = ver_parser.add_subparsers(dest="subcommand")

    ver_create = ver_sub.add_parser("create", help="Commit an immutable dataset version")
    ver_create.add_argument("--dataset-id", required=True, help="Target dataset ID")
    ver_create.add_argument("--semver", default="v1.0.0", help="Version tag (e.g. v1.0.0)")
    ver_create.add_argument("--desc", default="Release snapshot", help="Description")

    ver_compare = ver_sub.add_parser("compare", help="Compare two immutable versions")
    ver_compare.add_argument("--base", required=True, help="Base version ID")
    ver_compare.add_argument("--target", required=True, help="Target version ID")

    # quality
    q_parser = subparsers.add_parser("quality", help="Run automated data quality gates")
    q_sub = q_parser.add_subparsers(dest="subcommand")

    q_run = q_sub.add_parser("run", help="Run quality analysis for version")
    q_run.add_argument("--dataset-id", required=True, help="Dataset ID")
    q_run.add_argument("--version-id", required=True, help="Version ID")

    # provenance
    p_parser = subparsers.add_parser("provenance", help="Inspect lineage & provenance")
    p_sub = p_parser.add_subparsers(dest="subcommand")
    p_inspect = p_sub.add_parser("inspect", help="Inspect DAG lineage graph")
    p_inspect.add_argument("--dataset-id", required=True, help="Dataset ID")

    # manifest
    m_parser = subparsers.add_parser("manifest", help="Manifest verification")
    m_sub = m_parser.add_subparsers(dest="subcommand")
    m_verify = m_sub.add_parser("verify", help="Verify blob checksums against manifest")
    m_verify.add_argument("--version-id", required=True, help="Version ID")

    args = parser.parse_args()

    if args.command == "init":
        print(json.dumps({"status": "initialized", "message": "Storage repository and database ready."}, indent=2))
        sys.exit(0)

    elif args.command == "dataset":
        if args.subcommand == "list":
            datasets = DatasetService.list_datasets()
            print(json.dumps(datasets, indent=2))
        elif args.subcommand == "create":
            d = DatasetService.create_dataset(DatasetCreate(name=args.name, domain=args.domain, description=args.desc))
            print(json.dumps(d, indent=2))
        elif args.subcommand == "upload":
            path = Path(args.file)
            if not path.exists():
                print(f"Error: file not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            raw = path.read_bytes()
            digest, size = storage.store_bytes(raw)
            clean_name = args.logical_path or path.name
            record = DatasetService.add_file(args.dataset_id, clean_name, digest, size)
            print(json.dumps(record, indent=2))

    elif args.command == "version":
        if args.subcommand == "create":
            v = VersionService.create_version(args.dataset_id, VersionCreate(semver=args.semver, description=args.desc))
            print(json.dumps(v, indent=2))
        elif args.subcommand == "compare":
            diff = CompareService.compare_versions(args.base, args.target)
            print(json.dumps(diff, indent=2))

    elif args.command == "quality":
        if args.subcommand == "run":
            rep = QualityService.run_checks(args.dataset_id, args.version_id)
            print(json.dumps(rep, indent=2))

    elif args.command == "provenance":
        if args.subcommand == "inspect":
            lineage = ProvenanceService.get_lineage(args.dataset_id)
            print(json.dumps(lineage, indent=2))

    elif args.command == "manifest":
        if args.subcommand == "verify":
            v = VersionService.get_version(args.version_id)
            if not v:
                print(f"Error: version {args.version_id} not found", file=sys.stderr)
                sys.exit(1)
            results = []
            for f in v.get("files", []):
                valid = storage.verify_integrity(f["blob_hash"])
                results.append({"path": f["logical_path"], "hash": f["blob_hash"], "valid": valid})
            all_valid = all(r["valid"] for r in results)
            print(json.dumps({"version_id": args.version_id, "all_valid": all_valid, "files": results}, indent=2))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
