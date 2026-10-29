from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("DATASET_GOV_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORAGE_DIR = DATA_DIR / "storage"
BLOBS_DIR = STORAGE_DIR / "blobs"
TEMP_DIR = DATA_DIR / "tmp"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
BLOBS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "governance.sqlite3"
SECRET_KEY = os.getenv("SECRET_KEY", "gov-insecure-dev-secret-key-change-in-prod-sha256")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", 200 * 1024 * 1024)) # 200 MB
