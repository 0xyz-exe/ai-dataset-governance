import uuid
import json
import csv
import io
from typing import Dict, Any, List, Optional
from PIL import Image
from backend.app.db import db_session
from backend.app.storage import storage
from backend.app.services.version_service import VersionService

class QualityService:
    @staticmethod
    def run_checks(dataset_id: str, version_id: str) -> Dict[str, Any]:
        v = VersionService.get_version(version_id)
        if not v:
            raise ValueError("Target version not found")

        files = v.get("files", [])
        checks: List[Dict[str, Any]] = []

        dim_scores = {
            "completeness": 100.0,
            "validity": 100.0,
            "uniqueness": 100.0,
            "consistency": 100.0,
            "integrity": 100.0,
            "annotation_correctness": 100.0,
        }

        # 1. Integrity check
        corrupted_blobs = 0
        total_files = len(files)
        for f in files:
            is_valid = storage.verify_integrity(f["blob_hash"])
            if not is_valid:
                corrupted_blobs += 1

        if corrupted_blobs == 0:
            checks.append({
                "name": "storage_hash_integrity",
                "dimension": "integrity",
                "status": "passed",
                "score": 100.0,
                "message": f"All {total_files} file blobs verified against cryptographic SHA-256 digests."
            })
        else:
            dim_scores["integrity"] = max(0.0, 100.0 - (corrupted_blobs / max(1, total_files) * 100))
            checks.append({
                "name": "storage_hash_integrity",
                "dimension": "integrity",
                "status": "failed",
                "score": dim_scores["integrity"],
                "message": f"{corrupted_blobs} file(s) failed cryptographic checksum verification!"
            })

        # 2. File uniqueness check
        seen_hashes = set()
        duplicate_files = 0
        for f in files:
            if f["blob_hash"] in seen_hashes:
                duplicate_files += 1
            seen_hashes.add(f["blob_hash"])

        if duplicate_files == 0:
            checks.append({
                "name": "file_deduplication",
                "dimension": "uniqueness",
                "status": "passed",
                "score": 100.0,
                "message": "Zero duplicate file payloads detected across manifest."
            })
        else:
            dim_scores["uniqueness"] -= 20.0
            checks.append({
                "name": "file_deduplication",
                "dimension": "uniqueness",
                "status": "warning",
                "score": 80.0,
                "message": f"{duplicate_files} duplicate file payload(s) found in manifest."
            })

        # 3. Content validations (Tabular, YOLO, COCO, Images)
        for f in files:
            path = f["logical_path"].lower()
            try:
                raw_bytes = storage.read_bytes(f["blob_hash"])
            except Exception:
                continue

            # CSV validation
            if path.endswith(".csv"):
                try:
                    text = raw_bytes.decode("utf-8", errors="replace")
                    reader = list(csv.reader(io.StringIO(text)))
                    if len(reader) < 2:
                        dim_scores["completeness"] -= 15.0
                        checks.append({
                            "name": f"csv_rows_{f['logical_path']}",
                            "dimension": "completeness",
                            "status": "warning",
                            "score": 70.0,
                            "message": f"CSV {f['logical_path']} contains fewer than 2 rows."
                        })
                    else:
                        header = reader[0]
                        rows = reader[1:]
                        # Check missing values
                        null_cells = sum(row.count("") for row in rows)
                        total_cells = len(rows) * len(header)
                        null_pct = (null_cells / max(1, total_cells)) * 100

                        # Check duplicate rows
                        row_tuples = [tuple(r) for r in rows]
                        dupe_rows = len(row_tuples) - len(set(row_tuples))

                        if null_pct > 20:
                            dim_scores["completeness"] -= 20.0
                            checks.append({
                                "name": f"null_values_{f['logical_path']}",
                                "dimension": "completeness",
                                "status": "warning",
                                "score": 75.0,
                                "message": f"{f['logical_path']} has {null_pct:.1f}% missing or empty cells."
                            })
                        else:
                            checks.append({
                                "name": f"null_values_{f['logical_path']}",
                                "dimension": "completeness",
                                "status": "passed",
                                "score": 100.0,
                                "message": f"{f['logical_path']} missing cell rate is acceptable ({null_pct:.1f}%)."
                            })

                        if dupe_rows > 0:
                            dim_scores["uniqueness"] -= 15.0
                            checks.append({
                                "name": f"duplicate_rows_{f['logical_path']}",
                                "dimension": "uniqueness",
                                "status": "warning",
                                "score": 80.0,
                                "message": f"{f['logical_path']} contains {dupe_rows} duplicate row(s)."
                            })
                        else:
                            checks.append({
                                "name": f"duplicate_rows_{f['logical_path']}",
                                "dimension": "uniqueness",
                                "status": "passed",
                                "score": 100.0,
                                "message": f"{f['logical_path']} has no duplicate rows."
                            })
                except Exception as e:
                    dim_scores["validity"] -= 20.0
                    checks.append({
                        "name": f"csv_parse_error_{f['logical_path']}",
                        "dimension": "validity",
                        "status": "failed",
                        "score": 40.0,
                        "message": f"Failed to parse CSV {f['logical_path']}: {str(e)}"
                    })

            # Image validation
            elif path.endswith((".png", ".jpg", ".jpeg", ".webp")):
                try:
                    img = Image.open(io.BytesIO(raw_bytes))
                    img.verify()
                    checks.append({
                        "name": f"image_integrity_{f['logical_path']}",
                        "dimension": "validity",
                        "status": "passed",
                        "score": 100.0,
                        "message": f"Image {f['logical_path']} verified readable ({img.format}, {img.size[0]}x{img.size[1]})."
                    })
                except Exception as e:
                    dim_scores["validity"] -= 30.0
                    checks.append({
                        "name": f"image_corrupt_{f['logical_path']}",
                        "dimension": "validity",
                        "status": "failed",
                        "score": 0.0,
                        "message": f"Image {f['logical_path']} is corrupted or unreadable: {str(e)}"
                    })

            # YOLO annotation validation (.txt with coords)
            elif "labels" in path and path.endswith(".txt"):
                try:
                    text = raw_bytes.decode("utf-8", errors="replace").strip()
                    lines = [l for l in text.split("\n") if l.strip()]
                    invalid_coords = 0
                    for line in lines:
                        parts = line.split()
                        if len(parts) != 5:
                            invalid_coords += 1
                            continue
                        cls_id, xc, yc, w, h = parts
                        coords = [float(xc), float(yc), float(w), float(h)]
                        if any(c < 0.0 or c > 1.0 for c in coords):
                            invalid_coords += 1

                    if invalid_coords == 0:
                        checks.append({
                            "name": f"yolo_bbox_{f['logical_path']}",
                            "dimension": "annotation_correctness",
                            "status": "passed",
                            "score": 100.0,
                            "message": f"YOLO annotation {f['logical_path']} parsed: {len(lines)} normalized bbox(es)."
                        })
                    else:
                        dim_scores["annotation_correctness"] -= 25.0
                        checks.append({
                            "name": f"yolo_bbox_{f['logical_path']}",
                            "dimension": "annotation_correctness",
                            "status": "failed",
                            "score": 50.0,
                            "message": f"YOLO annotation {f['logical_path']} has {invalid_coords} invalid or unnormalized coordinates."
                        })
                except Exception as e:
                    dim_scores["annotation_correctness"] -= 30.0
                    checks.append({
                        "name": f"yolo_error_{f['logical_path']}",
                        "dimension": "annotation_correctness",
                        "status": "failed",
                        "score": 20.0,
                        "message": f"Failed to parse YOLO annotations {f['logical_path']}: {str(e)}"
                    })

            # COCO JSON validation
            elif path.endswith(".json") and any(k in path for k in ["coco", "instances", "annotations"]):
                try:
                    data = json.loads(raw_bytes.decode("utf-8"))
                    required_keys = {"images", "annotations", "categories"}
                    missing_coco_keys = required_keys - set(data.keys())
                    if missing_coco_keys:
                        dim_scores["annotation_correctness"] -= 30.0
                        checks.append({
                            "name": f"coco_schema_{f['logical_path']}",
                            "dimension": "annotation_correctness",
                            "status": "failed",
                            "score": 40.0,
                            "message": f"COCO file {f['logical_path']} missing standard keys: {missing_coco_keys}"
                        })
                    else:
                        checks.append({
                            "name": f"coco_schema_{f['logical_path']}",
                            "dimension": "annotation_correctness",
                            "status": "passed",
                            "score": 100.0,
                            "message": f"Valid COCO structure: {len(data['images'])} images, {len(data['annotations'])} annotations, {len(data['categories'])} categories."
                        })
                except Exception as e:
                    dim_scores["annotation_correctness"] -= 30.0
                    checks.append({
                        "name": f"coco_error_{f['logical_path']}",
                        "dimension": "annotation_correctness",
                        "status": "failed",
                        "score": 10.0,
                        "message": f"Invalid COCO JSON file: {str(e)}"
                    })

        # Clamp scores to 0-100
        for k in dim_scores:
            dim_scores[k] = max(0.0, min(100.0, dim_scores[k]))

        overall_score = round(sum(dim_scores.values()) / len(dim_scores), 1)
        passed_cnt = sum(1 for c in checks if c["status"] == "passed")
        failed_cnt = sum(1 for c in checks if c["status"] == "failed")
        warned_cnt = sum(1 for c in checks if c["status"] == "warning")

        status = "passed" if failed_cnt == 0 and overall_score >= 80.0 else ("warning" if failed_cnt == 0 else "failed")

        run_id = f"qr_{uuid.uuid4().hex[:12]}"

        report = {
            "overall_score": overall_score,
            "dimension_scores": dim_scores,
            "status": status,
            "checks_passed": passed_cnt,
            "checks_failed": failed_cnt,
            "checks_warned": warned_cnt,
            "checks": checks
        }

        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO quality_runs (id, dataset_id, version_id, overall_score, dimension_scores_json, status, checks_passed, checks_failed, checks_warned, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, dataset_id, version_id, overall_score, json.dumps(dim_scores), status, passed_cnt, failed_cnt, warned_cnt, json.dumps(report))
            )
            # Update version quality status
            conn.execute(
                "UPDATE dataset_versions SET quality_status = ? WHERE id = ?",
                (status, version_id)
            )

        return {
            "id": run_id,
            "dataset_id": dataset_id,
            "version_id": version_id,
            "overall_score": overall_score,
            "dimension_scores": dim_scores,
            "status": status,
            "checks_passed": passed_cnt,
            "checks_failed": failed_cnt,
            "checks_warned": warned_cnt,
            "checks": checks,
            "created_at": "now"
        }

    @staticmethod
    def list_runs(dataset_id: str, version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with db_session() as conn:
            query = "SELECT * FROM quality_runs WHERE dataset_id = ?"
            params = [dataset_id]
            if version_id:
                query += " AND version_id = ?"
                params.append(version_id)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, tuple(params)).fetchall()
            out = []
            for r in rows:
                item = dict(r)
                item["dimension_scores"] = json.loads(item.get("dimension_scores_json") or "{}")
                rep = json.loads(item.get("report_json") or "{}")
                item["checks"] = rep.get("checks", [])
                out.append(item)
            return out
