import sqlite3
import json
from contextlib import contextmanager
from typing import Generator
from backend.app.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    with db_session() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'engineer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            owner_id TEXT NOT NULL,
            tags TEXT,
            domain TEXT,
            task_type TEXT,
            license TEXT DEFAULT 'MIT',
            source_uri TEXT,
            visibility TEXT DEFAULT 'public',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS dataset_blobs (
            hash TEXT PRIMARY KEY,
            size_bytes INTEGER NOT NULL,
            mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ref_count INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS dataset_versions (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            version_num INTEGER NOT NULL,
            semver TEXT NOT NULL,
            description TEXT,
            creator_id TEXT NOT NULL,
            parent_version_id TEXT,
            manifest_hash TEXT NOT NULL,
            stats_json TEXT,
            schema_snapshot_json TEXT,
            quality_status TEXT DEFAULT 'unverified',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
            FOREIGN KEY (parent_version_id) REFERENCES dataset_versions (id),
            UNIQUE (dataset_id, version_num)
        );

        CREATE TABLE IF NOT EXISTS dataset_files (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            version_id TEXT,
            logical_path TEXT NOT NULL,
            blob_hash TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
            FOREIGN KEY (blob_hash) REFERENCES dataset_blobs (hash)
        );

        CREATE TABLE IF NOT EXISTS quality_runs (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            version_id TEXT NOT NULL,
            overall_score REAL NOT NULL,
            dimension_scores_json TEXT NOT NULL,
            status TEXT NOT NULL,
            checks_passed INTEGER DEFAULT 0,
            checks_failed INTEGER DEFAULT 0,
            checks_warned INTEGER DEFAULT 0,
            report_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES dataset_versions (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS provenance_events (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            version_id TEXT,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            operation TEXT NOT NULL,
            parameters_json TEXT,
            tool_name TEXT,
            tool_version TEXT,
            source_uri TEXT,
            parent_event_id TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS provenance_edges (
            id TEXT PRIMARY KEY,
            parent_id TEXT NOT NULL,
            child_id TEXT NOT NULL,
            artifact_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES provenance_events (id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES provenance_events (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS schemas (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            name TEXT NOT NULL,
            format_type TEXT NOT NULL,
            schema_json TEXT NOT NULL,
            version_num INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            dataset_id TEXT NOT NULL,
            version_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT,
            framework TEXT,
            hyperparameters_json TEXT,
            metrics_json TEXT,
            git_commit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES dataset_versions (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS governance_policies (
            id TEXT PRIMARY KEY,
            dataset_id TEXT,
            policy_type TEXT NOT NULL,
            rules_json TEXT NOT NULL,
            is_enforced INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details_json TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT OR IGNORE INTO users (id, email, full_name, password_hash, role)
        VALUES ('usr_default', 'admin@datasetgov.local', 'Default Administrator', 'hash_dev_default', 'admin');
        """)
