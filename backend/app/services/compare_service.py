from typing import Dict, Any, List
from backend.app.services.version_service import VersionService

class CompareService:
    @staticmethod
    def compare_versions(base_version_id: str, target_version_id: str) -> Dict[str, Any]:
        base_v = VersionService.get_version(base_version_id)
        target_v = VersionService.get_version(target_version_id)

        if not base_v or not target_v:
            raise ValueError("One or both versions not found")

        base_files = {f["logical_path"]: f for f in base_v.get("files", [])}
        target_files = {f["logical_path"]: f for f in target_v.get("files", [])}

        added = []
        removed = []
        modified = []
        unchanged = []

        for path, tf in target_files.items():
            if path not in base_files:
                added.append(tf)
            else:
                bf = base_files[path]
                if bf["blob_hash"] != tf["blob_hash"]:
                    modified.append({
                        "logical_path": path,
                        "old_hash": bf["blob_hash"],
                        "new_hash": tf["blob_hash"],
                        "old_size": bf["size_bytes"],
                        "new_size": tf["size_bytes"],
                        "size_delta": tf["size_bytes"] - bf["size_bytes"]
                    })
                else:
                    unchanged.append(tf)

        for path, bf in base_files.items():
            if path not in target_files:
                removed.append(bf)

        base_size = sum(f["size_bytes"] for f in base_files.values())
        target_size = sum(f["size_bytes"] for f in target_files.values())

        # Schema comparison
        schema_changes = []
        if len(added) > 0:
            schema_changes.append(f"Added {len(added)} file(s) into target version")
        if len(removed) > 0:
            schema_changes.append(f"Removed {len(removed)} file(s) from target version")
        if len(modified) > 0:
            schema_changes.append(f"Modified {len(modified)} file(s) across revisions")

        return {
            "base_version_id": base_version_id,
            "target_version_id": target_version_id,
            "base_semver": base_v.get("semver", ""),
            "target_semver": target_v.get("semver", ""),
            "added_files": added,
            "removed_files": removed,
            "modified_files": modified,
            "unchanged_files": unchanged,
            "size_delta_bytes": target_size - base_size,
            "file_count_delta": len(target_files) - len(base_files),
            "schema_changes": schema_changes,
            "quality_delta": {
                "base_status": base_v.get("quality_status", "unverified"),
                "target_status": target_v.get("quality_status", "unverified")
            }
        }
