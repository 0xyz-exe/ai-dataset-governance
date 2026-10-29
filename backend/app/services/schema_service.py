import uuid
import json
import csv
import io
from typing import Dict, Any, List, Optional
from backend.app.db import db_session
from backend.app.schemas import SchemaCreate

class SchemaService:
    @staticmethod
    def register_schema(dataset_id: str, data: SchemaCreate) -> Dict[str, Any]:
        schema_id = f"sch_{uuid.uuid4().hex[:12]}"

        with db_session() as conn:
            # Check last version
            last_s = conn.execute(
                "SELECT version_num FROM schemas WHERE dataset_id = ? AND name = ? ORDER BY version_num DESC LIMIT 1",
                (dataset_id, data.name)
            ).fetchone()
            next_ver = (last_s["version_num"] + 1) if last_s else 1

            conn.execute(
                """
                INSERT INTO schemas (id, dataset_id, name, format_type, schema_json, version_num, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (schema_id, dataset_id, data.name, data.format_type, json.dumps(data.schema_def), next_ver)
            )

        return SchemaService.get_schema(schema_id)

    @staticmethod
    def get_schema(schema_id: str) -> Dict[str, Any]:
        with db_session() as conn:
            r = conn.execute("SELECT * FROM schemas WHERE id = ?", (schema_id,)).fetchone()
            if not r:
                raise ValueError("Schema not found")
            res = dict(r)
            res["schema_def"] = json.loads(res.get("schema_json") or "{}")
            return res

    @staticmethod
    def list_schemas(dataset_id: str) -> List[Dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT id FROM schemas WHERE dataset_id = ? ORDER BY created_at DESC", (dataset_id,)).fetchall()
            return [SchemaService.get_schema(r["id"]) for r in rows]

    @staticmethod
    def detect_breaking_changes(old_schema_def: Dict[str, Any], new_schema_def: Dict[str, Any]) -> List[str]:
        """Detects breaking schema evolutions between two schema definitions."""
        breaking = []
        old_fields = {f["name"]: f for f in old_schema_def.get("fields", [])}
        new_fields = {f["name"]: f for f in new_schema_def.get("fields", [])}

        # Check removed fields
        for name, of in old_fields.items():
            if name not in new_fields:
                if of.get("required", False):
                    breaking.append(f"Breaking: Required field '{name}' was removed in target schema.")
                else:
                    breaking.append(f"Notice: Optional field '{name}' was removed.")

        # Check type changes and nullability changes
        for name, nf in new_fields.items():
            if name in old_fields:
                of = old_fields[name]
                if of.get("type") != nf.get("type"):
                    breaking.append(f"Breaking: Field '{name}' changed type from '{of.get('type')}' to '{nf.get('type')}'.")
                if of.get("nullable", True) and not nf.get("nullable", True):
                    breaking.append(f"Breaking: Field '{name}' changed from nullable to non-nullable (required).")

        return breaking

    @staticmethod
    def infer_schema_from_csv(csv_content: str, name: str = "default_csv_schema") -> Dict[str, Any]:
        reader = list(csv.reader(io.StringIO(csv_content.strip())))
        if not reader:
            return {"name": name, "format": "csv", "fields": []}

        header = reader[0]
        sample_rows = reader[1:100]

        fields = []
        for col_idx, col_name in enumerate(header):
            has_null = False
            types = set()
            for r in sample_rows:
                if col_idx < len(r):
                    val = r[col_idx].strip()
                    if val == "":
                        has_null = True
                    elif val.isdigit():
                        types.add("integer")
                    else:
                        try:
                            float(val)
                            types.add("float")
                        except ValueError:
                            types.add("string")
                else:
                    has_null = True

            inferred_type = "string"
            if len(types) == 1:
                inferred_type = list(types)[0]
            elif types == {"integer", "float"}:
                inferred_type = "float"

            fields.append({
                "name": col_name,
                "type": inferred_type,
                "nullable": has_null,
                "required": not has_null
            })

        return {
            "name": name,
            "format": "csv",
            "field_count": len(fields),
            "fields": fields
        }
