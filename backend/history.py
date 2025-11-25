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
                summary_url TEXT,
                summary_text TEXT,
                srt_text TEXT,
                status TEXT,
                meta TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # Add summary_url/summary_text if missing
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(history)")}
        if "summary_url" not in cols:
            conn.execute("ALTER TABLE history ADD COLUMN summary_url TEXT")
        if "summary_text" not in cols:
            conn.execute("ALTER TABLE history ADD COLUMN summary_text TEXT")
        if "srt_text" not in cols:
            conn.execute("ALTER TABLE history ADD COLUMN srt_text TEXT")

        # Populate summary_text for rows that have summary_url but empty summary_text
        try:
            cur = conn.execute("SELECT id, summary_url, summary_text FROM history WHERE (summary_text IS NULL OR summary_text = '') AND summary_url IS NOT NULL AND summary_url != ''")
            rows = cur.fetchall()
            for r in rows:
                sid = r["id"]
                s_url = r["summary_url"]
                s_text = _read_summary_text(s_url)
                if s_text:
                    conn.execute("UPDATE history SET summary_text = ? WHERE id = ?", (s_text, sid))
            conn.commit()
        except Exception:
            pass

        # Rebuild FTS on each init to avoid schema drift issues
        conn.execute("DROP TABLE IF EXISTS history_fts")
        conn.execute(
            """
            CREATE VIRTUAL TABLE history_fts USING fts5(
                service, original_file, download_url, summary_url, summary_text, srt_text, meta_text, created_at,
                content='history', content_rowid='id'
            )
            """
        )
        conn.commit()

        # Backfill FTS
        conn.execute(
            """
            INSERT INTO history_fts(rowid, service, original_file, download_url, summary_url, summary_text, srt_text, meta_text, created_at)
            SELECT id, service, original_file, download_url, summary_url, COALESCE(summary_text, ''), COALESCE(srt_text, ''), COALESCE(meta, ''), created_at FROM history
            """
        )
        conn.commit()


def _meta_to_text(meta: Optional[Dict[str, Any]]) -> str:
    if not meta:
        return ""
    try:
        return " ".join(f"{k}: {v}" for k, v in meta.items())
    except Exception:
        return ""


def _read_summary_text(summary_url: Optional[str]) -> str:
    if not summary_url:
        return ""
    try:
        # Expected form: /download/<filename>
        name = Path(summary_url).name
        candidates = [Path("processed") / name, Path(summary_url)]
        for p in candidates:
            if p.exists():
                return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return ""

def _read_srt_text(subtitle_url: Optional[str]) -> str:
    if not subtitle_url:
        return ""
    try:
        name = Path(subtitle_url).name
        candidates = [Path("processed") / name, Path(subtitle_url)]
        for p in candidates:
            if p.exists():
                return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return ""


def add_history(service: str, original_file: str, download_url: Optional[str], status: str = "success", meta: Optional[Dict[str, Any]] = None, summary_url: Optional[str] = None, summary_text: Optional[str] = None):
    meta_json = json.dumps(meta or {})
    meta_text = _meta_to_text(meta)
    subtitle_url = ""
    if meta and isinstance(meta, dict):
        subtitle_url = meta.get("subtitle_url", "") or meta.get("subtitle_file", "")
    summary_txt = summary_text if (summary_text not in (None, "")) else _read_summary_text(summary_url)
    srt_txt = _read_srt_text(subtitle_url)
    created = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO history (service, original_file, download_url, summary_url, summary_text, srt_text, status, meta, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                service,
                original_file,
                download_url or "",
                summary_url or "",
                summary_txt,
                srt_txt,
                status,
                meta_json,
                created
            )
        )
        rowid = cur.lastrowid
        conn.execute(
            """
            INSERT INTO history_fts(rowid, service, original_file, download_url, summary_url, summary_text, srt_text, meta_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rowid, service, original_file, download_url or "", summary_url or "", summary_txt, srt_txt, meta_text, created)
        )
        conn.commit()


def get_history(limit: int = 50) -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT id, service, original_file, download_url, summary_url, summary_text, status, meta, created_at FROM history ORDER BY id DESC LIMIT ?",
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


def search_history(query: str, limit: int = 30) -> List[Dict[str, Any]]:
    if not query:
        return []
    with _get_conn() as conn:
        try:
            cur = conn.execute(
                """
                SELECT h.id, h.service, h.original_file, h.download_url, h.summary_url, h.summary_text, h.status, h.meta, h.created_at
                FROM history_fts f
                JOIN history h ON h.id = f.rowid
                WHERE history_fts MATCH ?
                ORDER BY h.id DESC
                LIMIT ?
                """,
                (query, limit)
            )
        except Exception:
            # fallback to LIKE search
            like = f"%{query}%"
            cur = conn.execute(
                """
                SELECT id, service, original_file, download_url, summary_url, summary_text, srt_text, status, meta, created_at
                FROM history
                WHERE service LIKE ? OR original_file LIKE ? OR meta LIKE ? OR summary_url LIKE ? OR summary_text LIKE ? OR srt_text LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (like, like, like, like, like, like, limit)
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
