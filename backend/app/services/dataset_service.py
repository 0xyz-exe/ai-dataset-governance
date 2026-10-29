import uuid
import json
import re
from typing import List, Optional, Dict, Any
from backend.app.db import db_session
from backend.app.schemas import DatasetCreate, DatasetUpdate

def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", slug)

class DatasetService:
    @staticmethod
    def create_dataset(data: DatasetCreate, owner_id: str = "usr_default") -> Dict[str, Any]:
        dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
        base_slug = slugify(data.name)
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        tags_str = json.dumps(data.tags or [])
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO datasets (id, name, slug, description, owner_id, tags, domain, task_type, license, source_uri, visibility, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (dataset_id, data.name, slug, data.description, owner_id, tags_str, data.domain, data.task_type, data.license, data.source_uri, data.visibility)
            )
        res = DatasetService.get_dataset(dataset_id)
        if not res:
            raise RuntimeError("Failed to create dataset")
        return res

    @staticmethod
    def get_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM datasets WHERE id = ? OR slug = ?", (dataset_id, dataset_id)).fetchone()
            if not row:
                return None

            d = dict(row)
            d["tags"] = json.loads(d.get("tags") or "[]")

            # Get version count and latest version
            v_rows = conn.execute("SELECT id, semver, quality_status FROM dataset_versions WHERE dataset_id = ? ORDER BY version_num DESC", (d["id"],)).fetchall()
            d["total_versions"] = len(v_rows)
            d["latest_version"] = v_rows[0]["semver"] if v_rows else None
            d["quality_status"] = v_rows[0]["quality_status"] if v_rows else "unverified"

            # Get files summary
            f_rows = conn.execute("SELECT count(*) as count, coalesce(sum(size_bytes), 0) as total_size FROM dataset_files WHERE dataset_id = ?", (d["id"],)).fetchone()
            d["total_files"] = f_rows["count"] if f_rows else 0
            d["total_size_bytes"] = f_rows["total_size"] if f_rows else 0

            return d

    @staticmethod
    def list_datasets(domain: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        with db_session() as conn:
            query = "SELECT id FROM datasets WHERE status != 'archived'"
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain)
            if search:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
            query += " ORDER BY updated_at DESC"

            rows = conn.execute(query, tuple(params)).fetchall()
            out = []
            for r in rows:
                item = DatasetService.get_dataset(r["id"])
                if item:
                    out.append(item)
            return out

    @staticmethod
    def add_file(dataset_id: str, logical_path: str, blob_hash: str, size_bytes: int, version_id: Optional[str] = None) -> Dict[str, Any]:
        file_id = f"f_{uuid.uuid4().hex[:12]}"
        with db_session() as conn:
            # Upsert blob record
            conn.execute(
                """
                INSERT INTO dataset_blobs (hash, size_bytes, ref_count)
                VALUES (?, ?, 1)
                ON CONFLICT(hash) DO UPDATE SET ref_count = ref_count + 1
                """,
                (blob_hash, size_bytes)
            )
            conn.execute(
                """
                INSERT INTO dataset_files (id, dataset_id, version_id, logical_path, blob_hash, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (file_id, dataset_id, version_id, logical_path, blob_hash, size_bytes)
            )
            conn.execute("UPDATE datasets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (dataset_id,))

        return {
            "id": file_id,
            "dataset_id": dataset_id,
            "version_id": version_id,
            "logical_path": logical_path,
            "blob_hash": blob_hash,
            "size_bytes": size_bytes
        }

    @staticmethod
    def list_files(dataset_id: str, version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with db_session() as conn:
            if version_id:
                rows = conn.execute(
                    "SELECT * FROM dataset_files WHERE dataset_id = ? AND version_id = ? ORDER BY logical_path ASC",
                    (dataset_id, version_id)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM dataset_files WHERE dataset_id = ? ORDER BY created_at DESC",
                    (dataset_id,)
                ).fetchall()
            return [dict(r) for r in rows]
