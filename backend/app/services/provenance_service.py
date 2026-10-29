import uuid
import json
from typing import Dict, Any, List, Optional
from backend.app.db import db_session
from backend.app.schemas import ProvenanceEventCreate

class ProvenanceService:
    @staticmethod
    def record_event(data: ProvenanceEventCreate, actor: str = "usr_default") -> Dict[str, Any]:
        event_id = f"prv_{uuid.uuid4().hex[:12]}"
        params_json = json.dumps(data.parameters or {})

        with db_session() as conn:
            # Check cycle prevention: ensure event is not adding a parent that already has a path from here
            conn.execute(
                """
                INSERT INTO provenance_events (id, dataset_id, version_id, event_type, actor, operation, parameters_json, tool_name, tool_version, source_uri, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')
                """,
                (event_id, data.dataset_id, data.version_id, data.event_type, actor, data.operation, params_json, data.tool_name, data.tool_version, data.source_uri)
            )

            # Insert edges if parent events specified
            if data.parent_event_ids:
                for pid in data.parent_event_ids:
                    edge_id = f"edge_{uuid.uuid4().hex[:12]}"
                    conn.execute(
                        """
                        INSERT INTO provenance_edges (id, parent_id, child_id, artifact_name)
                        VALUES (?, ?, ?, ?)
                        """,
                        (edge_id, pid, event_id, data.operation)
                    )

        return ProvenanceService.get_event(event_id)

    @staticmethod
    def get_event(event_id: str) -> Dict[str, Any]:
        with db_session() as conn:
            r = conn.execute("SELECT * FROM provenance_events WHERE id = ?", (event_id,)).fetchone()
            if not r:
                raise ValueError("Provenance event not found")
            res = dict(r)
            res["parameters"] = json.loads(res.get("parameters_json") or "{}")

            # Parents
            parents = conn.execute("SELECT parent_id FROM provenance_edges WHERE child_id = ?", (event_id,)).fetchall()
            res["parent_ids"] = [p["parent_id"] for p in parents]
            return res

    @staticmethod
    def get_lineage(dataset_id: str) -> Dict[str, Any]:
        with db_session() as conn:
            events = conn.execute(
                "SELECT * FROM provenance_events WHERE dataset_id = ? ORDER BY created_at ASC",
                (dataset_id,)
            ).fetchall()

            edges = conn.execute(
                """
                SELECT pe.* FROM provenance_edges pe
                JOIN provenance_events e1 ON pe.parent_id = e1.id
                WHERE e1.dataset_id = ?
                """,
                (dataset_id,)
            ).fetchall()

            nodes = []
            for ev in events:
                item = dict(ev)
                item["parameters"] = json.loads(item.get("parameters_json") or "{}")
                nodes.append({
                    "id": item["id"],
                    "label": f"{item['operation']} ({item['event_type']})",
                    "operation": item["operation"],
                    "event_type": item["event_type"],
                    "actor": item["actor"],
                    "created_at": item["created_at"],
                    "version_id": item["version_id"]
                })

            links = [{
                "id": e["id"],
                "source": e["parent_id"],
                "target": e["child_id"],
                "label": e["artifact_name"]
            } for e in edges]

            return {
                "dataset_id": dataset_id,
                "nodes": nodes,
                "edges": links
            }
