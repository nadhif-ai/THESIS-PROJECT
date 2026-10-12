"""Local administration state. Connections are short-lived and thread-safe."""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings


def now():
    return datetime.now(timezone.utc).isoformat()


def data_path():
    path = Path(get_settings().data_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


@contextmanager
def connection():
    with sqlite3.connect(data_path() / "admin.sqlite3", timeout=30) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        yield db


def initialize(recover_jobs=False):
    with connection() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, salt TEXT, password_hash TEXT);
        CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, expires REAL, csrf TEXT);
        CREATE TABLE IF NOT EXISTS versions (
          id TEXT PRIMARY KEY, namespace TEXT UNIQUE, status TEXT, created_at TEXT,
          manifest TEXT, records TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, kind TEXT, status TEXT, payload TEXT, result TEXT,
          error TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS conversations (
          id INTEGER PRIMARY KEY, session_id TEXT, channel TEXT, question TEXT,
          answer TEXT, usage TEXT, latency REAL, trace_id TEXT, created_at TEXT);
        CREATE INDEX IF NOT EXISTS conversation_session ON conversations(session_id, id);
        """)
        if recover_jobs:
            db.execute(
                "UPDATE jobs SET status='interrupted', error='Application restarted; rerun this job.' WHERE status IN ('running','queued')"
            )
            db.execute(
                "UPDATE versions SET status='failed', error='Indexing interrupted; retry indexing.' WHERE status='indexing'"
            )
        settings = get_settings()
        if not db.execute(
            "SELECT 1 FROM users WHERE name=?", (settings.admin_username,)
        ).fetchone():
            password = settings.admin_password or secrets.token_urlsafe(18)
            salt = secrets.token_hex(16)
            db.execute(
                "INSERT INTO users VALUES (?,?,?)",
                (settings.admin_username, salt, hash_password(password, salt)),
            )
            if not settings.admin_password:
                credentials = data_path() / "admin-credentials.txt"
                credentials.write_text(
                    f"Username: {settings.admin_username}\nPassword: {password}\n"
                )
                credentials.chmod(0o600)
        if not db.execute(
            "SELECT 1 FROM settings WHERE key='history_imported'"
        ).fetchone():
            history = Path("dataset/admin_chat_history.json")
            if history.exists():
                for row in reversed(json.loads(history.read_text())):
                    session = row.get("session_id", "")
                    db.execute(
                        "INSERT INTO conversations (session_id,channel,question,answer,usage,created_at) VALUES (?,?,?,?,?,?)",
                        (
                            session,
                            "whatsapp" if session.startswith("wa_") else "api",
                            row.get("question", ""),
                            row.get("answer", ""),
                            "{}",
                            row.get("timestamp", now()),
                        ),
                    )
            db.execute(
                "INSERT INTO settings VALUES (?,?)", ("history_imported", "true")
            )


def hash_password(password, salt):
    return hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
    ).hex()


def get_setting(key, default=None):
    with connection() as db:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default


def set_setting(key, value):
    with connection() as db:
        db.execute(
            "INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value))
        )


def decode_version(row):
    item = dict(row)
    item["manifest"] = json.loads(item["manifest"])
    item["records"] = json.loads(item["records"])
    return item


def versions():
    with connection() as db:
        rows = db.execute("SELECT * FROM versions ORDER BY created_at DESC").fetchall()
    return [decode_version(row) for row in rows]


def version(version_id=None):
    version_id = version_id or get_setting("published_version")
    with connection() as db:
        row = db.execute("SELECT * FROM versions WHERE id=?", (version_id,)).fetchone()
    if not row:
        raise ValueError("Knowledge version not found.")
    return decode_version(row)


def save_version(item):
    with connection() as db:
        db.execute(
            "INSERT OR REPLACE INTO versions VALUES (?,?,?,?,?,?,?)",
            (
                item["id"],
                item["namespace"],
                item["status"],
                item["created_at"],
                json.dumps(item["manifest"]),
                json.dumps(item["records"]),
                item.get("error"),
            ),
        )


def publish(version_id):
    with connection() as db:
        row = db.execute(
            "SELECT status FROM versions WHERE id=?", (version_id,)
        ).fetchone()
        if not row or row["status"] not in ("ready", "published"):
            raise ValueError("Only fully indexed, ready versions can be published.")
        db.execute("UPDATE versions SET status='ready' WHERE status='published'")
        db.execute("UPDATE versions SET status='published' WHERE id=?", (version_id,))
        db.execute(
            "INSERT OR REPLACE INTO settings VALUES (?,?)",
            ("published_version", json.dumps(version_id)),
        )


def record_conversation(
    session_id, channel, question, answer, usage=None, latency=0, trace_id=None
):
    with connection() as db:
        db.execute(
            "INSERT INTO conversations (session_id,channel,question,answer,usage,latency,trace_id,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                session_id,
                channel,
                question,
                answer,
                json.dumps(usage or {}),
                latency,
                trace_id,
                now(),
            ),
        )


def conversations(channel=None, limit=200):
    with connection() as db:
        if channel:
            rows = db.execute(
                "SELECT * FROM conversations WHERE channel=? ORDER BY id DESC LIMIT ?",
                (channel, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(row, usage=json.loads(row["usage"] or "{}")) for row in rows]


def prompt_turns(session_id):
    boundary = get_setting("reset:" + session_id, 0)
    with connection() as db:
        rows = db.execute(
            "SELECT question,answer FROM conversations WHERE session_id=? AND id>? ORDER BY id DESC LIMIT 2",
            (session_id, boundary),
        ).fetchall()
    return [(r["question"], r["answer"]) for r in reversed(rows)]


def clear_session(session_id):
    with connection() as db:
        last = (
            db.execute(
                "SELECT MAX(id) FROM conversations WHERE session_id=?", (session_id,)
            ).fetchone()[0]
            or 0
        )
    set_setting("reset:" + session_id, last)
    return bool(last)
