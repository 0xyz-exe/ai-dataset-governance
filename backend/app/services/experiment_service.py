import uuid
import json
from typing import Dict, Any, List, Optional
from backend.app.db import db_session
from backend.app.schemas import ExperimentCreate

class ExperimentService:
    @staticmethod
    def register_experiment(data: ExperimentCreate) -> Dict[str, Any]:
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"

        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO experiments (id, name, description, dataset_id, version_id, model_name, model_version, framework, hyperparameters_json, metrics_json, git_commit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exp_id,
                    data.name,
                    data.description,
                    data.dataset_id,
                    data.version_id,
                    data.model_name,
                    data.model_version,
                    data.framework,
                    json.dumps(data.hyperparameters or {}),
                    json.dumps(data.metrics or {}),
                    data.git_commit
                )
            )

        return ExperimentService.get_experiment(exp_id)

    @staticmethod
    def get_experiment(exp_id: str) -> Dict[str, Any]:
        with db_session() as conn:
            r = conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()
            if not r:
                raise ValueError("Experiment not found")
            res = dict(r)
            res["hyperparameters"] = json.loads(res.get("hyperparameters_json") or "{}")
            res["metrics"] = json.loads(res.get("metrics_json") or "{}")
            return res

    @staticmethod
    def list_experiments(dataset_id: Optional[str] = None, version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with db_session() as conn:
            query = "SELECT id FROM experiments WHERE 1=1"
            params = []
            if dataset_id:
                query += " AND dataset_id = ?"
                params.append(dataset_id)
            if version_id:
                query += " AND version_id = ?"
                params.append(version_id)
            query += " ORDER BY created_at DESC"

            rows = conn.execute(query, tuple(params)).fetchall()
            return [ExperimentService.get_experiment(r["id"]) for r in rows]
