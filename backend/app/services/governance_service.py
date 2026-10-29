import uuid
import json
from typing import Dict, Any, List, Optional
from backend.app.db import db_session

class GovernanceService:
    @staticmethod
    def log_audit(actor: str, action: str, resource_type: str, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = "127.0.0.1") -> Dict[str, Any]:
        log_id = f"aud_{uuid.uuid4().hex[:12]}"
        details_json = json.dumps(details or {})

        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (id, actor, action, resource_type, resource_id, details_json, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (log_id, actor, action, resource_type, resource_id, details_json, ip_address)
            )

        return {
            "id": log_id,
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": "now"
        }

    @staticmethod
    def list_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            out = []
            for r in rows:
                item = dict(r)
                item["details"] = json.loads(item.get("details_json") or "{}")
                out.append(item)
            return out

    @staticmethod
    def check_license_compliance(license_name: str) -> Dict[str, Any]:
        permissive = ["MIT", "Apache-2.0", "BSD-3-Clause", "CC0-1.0", "CC-BY-4.0"]
        copyleft = ["GPL-3.0", "AGPL-3.0", "CC-BY-SA-4.0"]
        commercial_risk = ["CC-BY-NC-4.0", "Non-Commercial", "Proprietary", "Unknown"]

        lic = (license_name or "").strip()
        if lic in permissive:
            return {"license": lic, "status": "approved", "commercial_use": True, "risk_level": "low", "message": "Standard open-source permissive license suitable for model training & redistribution."}
        elif lic in copyleft:
            return {"license": lic, "status": "conditional", "commercial_use": True, "risk_level": "medium", "message": "Copyleft license. Derivatives or trained models may require public disclosure under same terms."}
        else:
            return {"license": lic or "Unknown", "status": "restricted", "commercial_use": False, "risk_level": "high", "message": "Non-commercial or unverified license. Review required before training production models."}
