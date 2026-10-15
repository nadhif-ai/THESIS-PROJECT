"""Administration persistence. SQL and transaction ownership stay in this module."""

import hashlib
import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from app.config.settings import get_settings

_pool = None
_pool_lock = threading.RLock()


class StateUnavailable(RuntimeError):
    pass


class MaintenanceError(StateUnavailable):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def data_path():
    path = Path(get_settings().data_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def open_pool():
    global _pool
    with _pool_lock:
        if _pool is not None:
            return
        dsn = get_settings().database_url
        if not dsn:
            raise StateUnavailable(
                "DATABASE_URL is required; local state fallback is disabled."
            )
        try:
            options = conninfo_to_dict(dsn)
            local = options.get("host") in ("127.0.0.1", "localhost", "::1")
            kwargs = dict(
                row_factory=dict_row, prepare_threshold=None, connect_timeout=5
            )
            kwargs["sslmode"] = "disable" if local else "require"
            pool = ConnectionPool(
                dsn,
                min_size=0,
                max_size=2,
                timeout=5,
                max_waiting=20,
                open=False,
                kwargs=kwargs,
                check=ConnectionPool.check_connection,
            )
            pool.open()
            _pool = pool
        except (psycopg.Error, ValueError):
            raise StateUnavailable(
                "PostgreSQL connection configuration is invalid."
            ) from None


def close_pool():
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None


@contextmanager
def _connection(purpose=None):
    open_pool()
    try:
        with _pool.connection() as db:
            db.execute("SET LOCAL statement_timeout='30s'")
            db.execute("SET LOCAL lock_timeout='5s'")
            if purpose:
                control = db.execute(
                    "SELECT * FROM chatbot.runtime_control WHERE id=1 FOR UPDATE"
                ).fetchone()
                allowed = (("intake",) if purpose == "reconciliation" else
                           ("intake", "live") if purpose == "intake" else ("live",))
                if not control or control["mode"] not in allowed:
                    raise MaintenanceError(
                        "Chatbot maintenance is active. Please try again later."
                    )
                if control["cutover_started_at"] and not control["first_live_write_at"]:
                    db.execute(
                        "UPDATE chatbot.runtime_control SET first_live_write_at=%s WHERE id=1",
                        (now(),),
                    )
            yield db
    except (psycopg.Error, PoolTimeout):
        raise StateUnavailable(
            "Administration database is unavailable; inspect the private backend log."
        ) from None


def check_ready():
    with _connection() as db:
        if (
            db.execute("SELECT current_user AS name").fetchone()["name"]
            != "chatbot_app"
        ):
            raise StateUnavailable(
                "Use the restricted chatbot_app database role for runtime."
            )
        versions = db.execute(
            "SELECT version FROM chatbot.schema_migrations ORDER BY version"
        ).fetchall()
        if [r["version"] for r in versions] != [1]:
            raise StateUnavailable(
                "Apply the expected administration schema migration before startup."
            )
        if not db.execute(
            "SELECT 1 FROM chatbot.runtime_control WHERE id=1"
        ).fetchone():
            raise StateUnavailable("Administration control state is missing.")
        row = db.execute(
            "SELECT value FROM chatbot.settings WHERE key='published_version'"
        ).fetchone()
        if not row:
            raise StateUnavailable("Import administration data before startup.")
        item = db.execute(
            "SELECT 1 FROM chatbot.versions WHERE id=%s AND status='published'",
            (json.loads(row["value"]),),
        ).fetchone()
        if not item:
            raise StateUnavailable("Published knowledge selection is inconsistent.")


def get_runtime_mode():
    with _connection() as db:
        row = db.execute(
            "SELECT mode FROM chatbot.runtime_control WHERE id=1"
        ).fetchone()
    if not row:
        raise StateUnavailable("Administration control state is missing.")
    return row["mode"]


def require_live():
    if get_runtime_mode() != "live":
        raise MaintenanceError("Chatbot maintenance is active. Please try again later.")


def hash_password(password, salt):
    return hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
    ).hex()


def get_user(name):
    with _connection() as db:
        return db.execute(
            "SELECT * FROM chatbot.users WHERE name=%s", (name,)
        ).fetchone()


def get_session(token_hash, at):
    with _connection() as db:
        return db.execute(
            "SELECT * FROM chatbot.sessions WHERE token_hash=%s AND expires>%s",
            (token_hash, at),
        ).fetchone()


def create_session(token_hash, expires, csrf):
    with _connection("administration") as db:
        db.execute("DELETE FROM chatbot.sessions WHERE expires<%s", (time.time(),))
        db.execute(
            "INSERT INTO chatbot.sessions VALUES(%s,%s,%s)", (token_hash, expires, csrf)
        )


def delete_session(token_hash):
    with _connection("administration") as db:
        db.execute("DELETE FROM chatbot.sessions WHERE token_hash=%s", (token_hash,))


def login_allowed(client_hash, at):
    with _connection("administration") as db:
        db.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (client_hash,)
        )
        db.execute(
            "DELETE FROM chatbot.login_attempts WHERE client_hash=%s AND attempted_at<=%s",
            (client_hash, at - 300),
        )
        return (
            db.execute(
                "SELECT count(*) AS n FROM chatbot.login_attempts WHERE client_hash=%s",
                (client_hash,),
            ).fetchone()["n"]
            < 10
        )


def record_login_failure(client_hash, at):
    with _connection("administration") as db:
        db.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (client_hash,)
        )
        db.execute(
            "INSERT INTO chatbot.login_attempts VALUES(%s,%s)", (client_hash, at)
        )


def clear_login_failures(client_hash):
    with _connection("administration") as db:
        db.execute(
            "DELETE FROM chatbot.login_attempts WHERE client_hash=%s", (client_hash,)
        )


def get_setting(key, default=None):
    with _connection() as db:
        row = db.execute(
            "SELECT value FROM chatbot.settings WHERE key=%s", (key,)
        ).fetchone()
    return json.loads(row["value"]) if row else default


def set_setting(key, value):
    with _connection("administration") as db:
        db.execute(
            "INSERT INTO chatbot.settings VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )


def decode_version(row):
    item = dict(row)
    item["manifest"] = json.loads(item["manifest"])
    item["records"] = json.loads(item["records"])
    return item


def versions():
    with _connection() as db:
        rows = db.execute(
            "SELECT * FROM chatbot.versions ORDER BY created_at DESC"
        ).fetchall()
    return [decode_version(r) for r in rows]


def version(version_id=None):
    version_id = version_id or get_setting("published_version")
    with _connection() as db:
        row = db.execute(
            "SELECT * FROM chatbot.versions WHERE id=%s", (version_id,)
        ).fetchone()
    if not row:
        raise ValueError("Knowledge version not found.")
    return decode_version(row)


def save_version(item):
    with _connection("administration") as db:
        db.execute(
            """INSERT INTO chatbot.versions(id,namespace,status,created_at,manifest,records,error)
          VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
          namespace=excluded.namespace,status=excluded.status,created_at=excluded.created_at,
          manifest=excluded.manifest,records=excluded.records,error=excluded.error""",
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
    with _connection("administration") as db:
        row = db.execute(
            "SELECT status FROM chatbot.versions WHERE id=%s FOR UPDATE", (version_id,)
        ).fetchone()
        if not row or row["status"] not in ("ready", "published"):
            raise ValueError("Only fully indexed, ready versions can be published.")
        db.execute(
            "UPDATE chatbot.versions SET status='ready' WHERE status='published'"
        )
        db.execute(
            "UPDATE chatbot.versions SET status='published' WHERE id=%s", (version_id,)
        )
        db.execute(
            "INSERT INTO chatbot.settings VALUES('published_version',%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (json.dumps(version_id),),
        )


def record_conversation(
    session_id, channel, question, answer, usage=None, latency=0, trace_id=None
):
    with _connection("execution") as db:
        db.execute(
            "INSERT INTO chatbot.conversations(session_id,channel,question,answer,usage,latency,trace_id,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
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
    with _connection() as db:
        if channel:
            rows = db.execute(
                "SELECT * FROM chatbot.conversations WHERE channel=%s ORDER BY id DESC LIMIT %s",
                (channel, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM chatbot.conversations ORDER BY id DESC LIMIT %s",
                (limit,),
            ).fetchall()
    return [dict(r, usage=json.loads(r["usage"] or "{}")) for r in rows]


def prompt_turns(session_id):
    boundary = get_setting("reset:" + session_id, 0)
    with _connection() as db:
        rows = db.execute(
            "SELECT question,answer FROM chatbot.conversations WHERE session_id=%s AND id>%s ORDER BY id DESC LIMIT 2",
            (session_id, boundary),
        ).fetchall()
    return [(r["question"], r["answer"]) for r in reversed(rows)]


def clear_session(session_id):
    with _connection("administration") as db:
        last = db.execute(
            "SELECT COALESCE(MAX(id),0) AS last FROM chatbot.conversations WHERE session_id=%s",
            (session_id,),
        ).fetchone()["last"]
        db.execute(
            "INSERT INTO chatbot.settings VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("reset:" + session_id, json.dumps(last)),
        )
    return bool(last)


def list_job_rows(limit=100):
    with _connection() as db:
        rows = db.execute(
            "SELECT * FROM chatbot.jobs ORDER BY created_at DESC LIMIT %s", (limit,)
        ).fetchall()
    return [
        dict(
            r,
            payload=json.loads(r["payload"]),
            result=json.loads(r["result"]) if r["result"] else None,
            progress=json.loads(r["progress"]),
        )
        for r in rows
    ]


def create_job_row(identifier, kind, payload):
    with _connection("administration") as db:
        db.execute(
            "INSERT INTO chatbot.jobs(id,kind,status,payload,created_at,updated_at) VALUES(%s,%s,%s,%s,%s,%s)",
            (identifier, kind, "queued", json.dumps(payload), now(), now()),
        )


def set_job_state(identifier, status, result=None, error=None):
    if status not in ("queued", "running", "completed", "failed", "interrupted"):
        raise ValueError("Invalid job state.")
    with _connection("execution") as db:
        db.execute(
            "UPDATE chatbot.jobs SET status=%s,result=%s,error=%s,updated_at=%s WHERE id=%s",
            (
                status,
                json.dumps(result) if result is not None else None,
                error,
                now(),
                identifier,
            ),
        )


def merge_job_progress(identifier, fields):
    with _connection("execution") as db:
        row = db.execute(
            "SELECT progress FROM chatbot.jobs WHERE id=%s FOR UPDATE", (identifier,)
        ).fetchone()
        if row:
            progress = json.loads(row["progress"])
            progress.update(fields)
            db.execute(
                "UPDATE chatbot.jobs SET progress=%s,updated_at=%s WHERE id=%s",
                (json.dumps(progress), now(), identifier),
            )


def _enqueue_inbox(db, session, message_id, sender, body, received_at=None):
    inserted = db.execute(
        """INSERT INTO chatbot.whatsapp_inbox(session,message_id,sender,body,status,reply_ids,created_at,updated_at)
        VALUES(%s,%s,%s,%s,'queued','[]',%s,%s) ON CONFLICT(session,message_id) DO NOTHING""",
        (session, message_id, sender, body, received_at or now(), now()),
    ).rowcount
    if not inserted:
        row = db.execute(
            "SELECT sender,body FROM chatbot.whatsapp_inbox WHERE session=%s AND message_id=%s",
            (session,message_id),
        ).fetchone()
        if row["sender"] != sender or row["body"] != body:
            raise ValueError("Duplicate WhatsApp ID has conflicting content; review before replay.")
    return bool(inserted)


def enqueue_inbox(session, message_id, sender, body, received_at=None):
    with _connection("intake") as db:
        return _enqueue_inbox(db,session,message_id,sender,body,received_at)


def reconcile_intake(session, messages, acknowledgements):
    inserted = 0
    with _connection("reconciliation") as db:
        for item in messages:
            inserted += _enqueue_inbox(db,session,**item)
        for message_id, ack in acknowledgements.items():
            _record_ack(db,message_id,ack)
    return inserted


def claim_inbox(session):
    with _connection("execution") as db:
        return db.execute(
            """WITH candidate AS (
            SELECT pending.session,pending.message_id FROM chatbot.whatsapp_inbox AS pending
            WHERE pending.session=%s AND pending.status='queued'
            AND NOT EXISTS(SELECT 1 FROM chatbot.whatsapp_inbox AS active
               WHERE active.session=pending.session AND active.sender=pending.sender AND active.status IN ('generating','sending'))
            ORDER BY pending.created_at,pending.message_id LIMIT 1 FOR UPDATE SKIP LOCKED)
            UPDATE chatbot.whatsapp_inbox AS inbox SET status='generating',updated_at=%s FROM candidate
            WHERE inbox.session=candidate.session AND inbox.message_id=candidate.message_id RETURNING inbox.*""",
            (session, now()),
        ).fetchone()


def update_inbox(session, message_id, fields):
    from psycopg import sql

    allowed = {"status", "answer", "media_url", "reply_ids", "error"}
    if not fields or not set(fields) <= allowed:
        raise ValueError("Invalid inbox update fields.")
    if "status" in fields and fields["status"] not in (
        "queued",
        "generating",
        "sending",
        "sent",
        "failed",
        "uncertain",
    ):
        raise ValueError("Invalid inbox state.")
    values = dict(fields, updated_at=now())
    assignments = sql.SQL(",").join(
        sql.SQL("{}=%s").format(sql.Identifier(k)) for k in values
    )
    with _connection("execution") as db:
        db.execute(
            sql.SQL(
                "UPDATE chatbot.whatsapp_inbox SET {} WHERE session=%s AND message_id=%s"
            ).format(assignments),
            (*values.values(), session, message_id),
        )


def get_inbox(session, message_id):
    with _connection() as db:
        return db.execute(
            "SELECT * FROM chatbot.whatsapp_inbox WHERE session=%s AND message_id=%s",
            (session, message_id),
        ).fetchone()


def inbox_rows(session):
    with _connection() as db:
        return db.execute(
            "SELECT * FROM chatbot.whatsapp_inbox WHERE session=%s ORDER BY created_at,message_id",
            (session,),
        ).fetchall()


def _record_ack(db, message_id, ack):
    if type(ack) is not int or not -1 <= ack <= 4:
        raise ValueError("Invalid WhatsApp acknowledgement.")
    db.execute(
        """INSERT INTO chatbot.whatsapp_receipts VALUES(%s,%s,%s)
        ON CONFLICT(message_id) DO UPDATE SET ack=GREATEST(chatbot.whatsapp_receipts.ack,excluded.ack),updated_at=excluded.updated_at""",
        (message_id,ack,now()),
    )


def record_ack(message_id, ack):
    with _connection("intake") as db:
        _record_ack(db,message_id,ack)


def whatsapp_observations(session):
    with _connection() as db:
        counts = db.execute(
            "SELECT status,count(*) AS n FROM chatbot.whatsapp_inbox WHERE session=%s GROUP BY status",
            (session,),
        ).fetchall()
        times = db.execute(
            "SELECT MAX(created_at) AS received,MAX(updated_at) FILTER(WHERE status='sent') AS sent FROM chatbot.whatsapp_inbox WHERE session=%s",
            (session,),
        ).fetchone()
        ack = db.execute(
            "SELECT MAX(updated_at) AS latest FROM chatbot.whatsapp_receipts"
        ).fetchone()["latest"]
    return dict(
        queue={r["status"]: r["n"] for r in counts},
        last_received_at=times["received"],
        last_sent_at=times["sent"],
        last_ack_at=ack,
        checked_at=now(),
    )
