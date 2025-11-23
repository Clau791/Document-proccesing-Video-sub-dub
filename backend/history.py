import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

DB_PATH = Path("processed/history.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                original_file TEXT,
                download_url TEXT,
                status TEXT,
                meta TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_history(service: str, original_file: str, download_url: Optional[str], status: str = "success", meta: Optional[Dict[str, Any]] = None):
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO history (service, original_file, download_url, status, meta, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                service,
                original_file,
                download_url or "",
                status,
                json.dumps(meta or {}),
                datetime.utcnow().isoformat()
            )
        )
        conn.commit()


def get_history(limit: int = 50) -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT id, service, original_file, download_url, status, meta, created_at FROM history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            item = dict(r)
            if item.get("meta"):
                try:
                    item["meta"] = json.loads(item["meta"])
                except Exception:
                    item["meta"] = {}
            result.append(item)
        return result


# initialize at import
init_db()
