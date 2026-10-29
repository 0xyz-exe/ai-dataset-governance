import uuid
import hashlib
import json
from typing import List, Optional, Dict, Any
from backend.app.db import db_session
from backend.app.schemas import VersionCreate
from backend.app.services.dataset_service import DatasetService

class VersionService:
    @staticmethod
    def create_version(dataset_id: str, data: VersionCreate, creator_id: str = "usr_default") -> Dict[str, Any]:
        with db_session() as conn:
            # Check dataset exists
            ds = conn.execute("SELECT id FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
            if not ds:
                raise ValueError("Dataset not found")

            # Determine next version number
            last_v = conn.execute(
                "SELECT version_num, id FROM dataset_versions WHERE dataset_id = ? ORDER BY version_num DESC LIMIT 1",
                (dataset_id,)
            ).fetchone()
            next_num = (last_v["version_num"] + 1) if last_v else 1
            parent_id = last_v["id"] if last_v else None

            # Get files for this version
            if data.file_ids:
                placeholders = ",".join(["?"] * len(data.file_ids))
                f_rows = conn.execute(
                    f"SELECT id, logical_path, blob_hash, size_bytes FROM dataset_files WHERE id IN ({placeholders}) AND dataset_id = ?",
                    (*data.file_ids, dataset_id)
                ).fetchall()
            else:
                # Use current files not yet bound to a version or all active files
                f_rows = conn.execute(
                    "SELECT id, logical_path, blob_hash, size_bytes FROM dataset_files WHERE dataset_id = ? AND version_id IS NULL",
                    (dataset_id,)
                ).fetchall()
                if not f_rows and parent_id:
                    # Inherit from parent version
                    f_rows = conn.execute(
                        "SELECT id, logical_path, blob_hash, size_bytes FROM dataset_files WHERE dataset_id = ? AND version_id = ?",
                        (dataset_id, parent_id)
                    ).fetchall()

            files_list = [dict(r) for r in f_rows]
            # Deterministic manifest calculation
            files_list_sorted = sorted(files_list, key=lambda x: x["logical_path"])
            manifest_dict = {
                "dataset_id": dataset_id,
                "version_num": next_num,
                "semver": data.semver,
                "files": [{"path": f["logical_path"], "hash": f["blob_hash"], "size": f["size_bytes"]} for f in files_list_sorted]
            }
            manifest_bytes = json.dumps(manifest_dict, sort_keys=True).encode("utf-8")
            manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()

            # Stats calculation
            total_size = sum(f["size_bytes"] for f in files_list)
            stats = {
                "file_count": len(files_list),
                "total_size_bytes": total_size,
                "manifest_hash": manifest_hash
            }

            version_id = f"ver_{uuid.uuid4().hex[:12]}"

            conn.execute(
                """
                INSERT INTO dataset_versions (id, dataset_id, version_num, semver, description, creator_id, parent_version_id, manifest_hash, stats_json, quality_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unverified')
                """,
                (version_id, dataset_id, next_num, data.semver, data.description, creator_id, parent_id, manifest_hash, json.dumps(stats))
            )

            # Link or duplicate file references for immutable snapshot
            for f in files_list:
                # Insert immutable snapshot record
                snap_id = f"f_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO dataset_files (id, dataset_id, version_id, logical_path, blob_hash, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (snap_id, dataset_id, version_id, f["logical_path"], f["blob_hash"], f["size_bytes"])
                )

            # Record provenance event
            conn.execute(
                """
                INSERT INTO provenance_events (id, dataset_id, version_id, event_type, actor, operation, parameters_json, tool_name, status)
                VALUES (?, ?, ?, 'version_created', ?, 'commit_version', ?, 'governance_engine', 'completed')
                """,
                (f"prv_{uuid.uuid4().hex[:12]}", dataset_id, version_id, creator_id, json.dumps({"semver": data.semver, "manifest_hash": manifest_hash}))
            )

            conn.execute("UPDATE datasets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (dataset_id,))

        res = VersionService.get_version(version_id)
        if not res:
            raise RuntimeError("Failed to retrieve created version")
        return res

    @staticmethod
    def get_version(version_id: str) -> Optional[Dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM dataset_versions WHERE id = ?", (version_id,)).fetchone()
            if not row:
                return None
            v = dict(row)
            v["stats"] = json.loads(v.get("stats_json") or "{}")
            v["schema_snapshot"] = json.loads(v.get("schema_snapshot_json") or "{}")

            # Load files
            f_rows = conn.execute("SELECT * FROM dataset_files WHERE version_id = ? ORDER BY logical_path ASC", (version_id,)).fetchall()
            v["files"] = [dict(r) for r in f_rows]
            return v

    @staticmethod
    def list_versions(dataset_id: str) -> List[Dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT id FROM dataset_versions WHERE dataset_id = ? ORDER BY version_num DESC", (dataset_id,)).fetchall()
            out = []
            for r in rows:
                v = VersionService.get_version(r["id"])
                if v:
                    out.append(v)
            return out

    @staticmethod
    def restore_version(dataset_id: str, version_id: str, user_id: str = "usr_default") -> Dict[str, Any]:
        """Restores an earlier version by creating a new version with the historical version's snapshot."""
        old_v = VersionService.get_version(version_id)
        if not old_v:
            raise ValueError("Target version not found")

        create_data = VersionCreate(
            semver=f"{old_v['semver']}-restored",
            description=f"Restored from version {old_v['semver']} (ID: {old_v['id']})",
            file_ids=[f["id"] for f in old_v["files"]]
        )
        return VersionService.create_version(dataset_id, create_data, creator_id=user_id)
