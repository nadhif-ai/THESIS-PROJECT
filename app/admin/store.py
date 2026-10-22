"""Administration persistence. SQL and transaction ownership stay in this module."""

import hashlib
import json
import logging
import threading
import time
import uuid
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
_IO_TIMEOUT = 35.0
_TRANSACTION_SETUP = """SET LOCAL statement_timeout='30s'; SET LOCAL lock_timeout='5s';
SET LOCAL idle_in_transaction_session_timeout='35s'"""


class _DatabaseConnection(psycopg.Connection):
    def wait(self, gen, interval=.1, timeout=None):
        # Server statement_timeout cannot release a socket whose response never arrives.
        timeout = _IO_TIMEOUT if timeout is None else min(timeout, _IO_TIMEOUT)
        try:
            return super().wait(gen, interval=interval, timeout=timeout)
        except psycopg.OperationalError:
            self.close()
            raise


def _check_connection(db):
    # A health query on every checkout adds a network round trip to every read.
    if db.closed or db.broken or time.monotonic() - getattr(db, "_admin_last_used", 0) >= 30:
        ConnectionPool.check_connection(db)


def _reconnect_failed(pool):
    if not pool.closed:
        logging.getLogger(__name__).warning("Database reconnect window exhausted; restarting connection recovery.")
        # Expired waiters can fill max_waiting and prevent new requests from growing an empty pool.
        pool.check()


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
                row_factory=dict_row, prepare_threshold=None, connect_timeout=5,
                autocommit=True, cursor_factory=psycopg.ClientCursor,
                keepalives=1, keepalives_idle=10, keepalives_interval=5,
                keepalives_count=3, tcp_user_timeout=20_000,
                application_name="chatbot-rag",
            )
            kwargs["sslmode"] = "disable" if local else "require"
            pool = ConnectionPool(
                dsn,
                connection_class=_DatabaseConnection,
                min_size=0,
                max_size=2,
                timeout=15,
                reconnect_timeout=15,
                max_waiting=20,
                open=False,
                kwargs=kwargs,
                check=_check_connection,
                reconnect_failed=_reconnect_failed,
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
def _connection(purpose=None, *, exclusive=False):
    open_pool()
    started = time.perf_counter()
    phase = "acquire"
    try:
        with _pool.connection() as db:
            phase = "transaction_setup"
            setup = "BEGIN; " + _TRANSACTION_SETUP
            if purpose:
                lock = "UPDATE" if exclusive else "SHARE"
                cursor = db.execute(setup + "; UPDATE chatbot.runtime_control SET first_live_write_at=CURRENT_TIMESTAMP::text "
                    "WHERE id=1 AND cutover_started_at IS NOT NULL AND first_live_write_at IS NULL AND mode<>'closed'; "
                    "SELECT * FROM chatbot.runtime_control WHERE id=1 FOR " + lock)
                for _ in range(5):
                    cursor.nextset()
                control = cursor.fetchone()
                allowed = (("intake",) if purpose == "reconciliation" else
                           ("intake", "live") if purpose == "intake" else ("live",))
                if not control or control["mode"] not in allowed:
                    raise MaintenanceError(
                        "Chatbot maintenance is active. Please try again later."
                    )
            else:
                db.execute(setup)
            phase = "operation"
            yield db
            phase = "commit"
        db._admin_last_used = time.monotonic()
    except (psycopg.Error, PoolTimeout) as error:
        logging.getLogger(__name__).warning(
            "Database failure phase=%s error=%s sqlstate=%s elapsed_ms=%.1f pool=%s",
            phase, type(error).__name__, error.sqlstate,
            (time.perf_counter() - started) * 1000, pool_stats(),
        )
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
        if [r["version"] for r in versions] != [1, 2]:
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
            return
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
    return admin_snapshot(token_hash, at, "me")


def create_session(token_hash, expires, csrf, client_hash=None):
    with _connection("administration") as db:
        db.execute(
            """DELETE FROM chatbot.login_attempts WHERE client_hash=%s;
            DELETE FROM chatbot.sessions WHERE expires<%s;
            INSERT INTO chatbot.sessions VALUES(%s,%s,%s)""",
            (client_hash, time.time(), token_hash, expires, csrf),
        )


def delete_session(token_hash):
    with _connection("administration") as db:
        db.execute("DELETE FROM chatbot.sessions WHERE token_hash=%s", (token_hash,))


def login_allowed(client_hash, at):
    return login_candidate(client_hash, at)[0]


def login_candidate(client_hash, at, name=None):
    with _connection("administration") as db:
        cursor = db.execute(
            """SELECT pg_advisory_xact_lock(hashtextextended(%s,0));
            DELETE FROM chatbot.login_attempts WHERE client_hash=%s AND attempted_at<=%s;
            SELECT count(*) AS n FROM chatbot.login_attempts WHERE client_hash=%s;
            SELECT * FROM chatbot.users WHERE name=%s""",
            (client_hash, client_hash, at - 300, client_hash, name),
        )
        cursor.nextset()
        cursor.nextset()
        allowed = cursor.fetchone()["n"] < 10
        cursor.nextset()
        return allowed, cursor.fetchone()


def record_login_failure(client_hash, at):
    with _connection("administration") as db:
        db.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (client_hash,)
        )
        db.execute(
            "INSERT INTO chatbot.login_attempts VALUES(%s,%s)", (client_hash, at)
        )


def get_setting(key, default=None):
    with _connection() as db:
        row = db.execute(
            "SELECT value FROM chatbot.settings WHERE key=%s", (key,)
        ).fetchone()
    return json.loads(row["value"]) if row else default


def set_setting(key, value):
    set_settings({key: value})


def get_settings_values(defaults):
    with _connection() as db:
        rows = db.execute(
            "SELECT key,value FROM chatbot.settings WHERE key=ANY(%s)", (list(defaults),)
        ).fetchall()
    return defaults | {row["key"]: json.loads(row["value"]) for row in rows}


def set_settings(values):
    with _connection("administration") as db:
        db.execute(
            """INSERT INTO chatbot.settings(key,value)
            SELECT key,value FROM jsonb_each_text(%s::jsonb)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (json.dumps({key: json.dumps(value) for key, value in values.items()}),),
        )


def _bot_replies_enabled(db):
    row = db.execute(
        "SELECT value FROM chatbot.settings WHERE key='bot_replies_enabled'"
    ).fetchone()
    return row is None or json.loads(row["value"]) is True


def set_bot_replies(enabled):
    # Pause must serialize with intake and send claims; unrelated writes share the gate.
    with _connection("administration", exclusive=True) as db:
        db.execute(
            """INSERT INTO chatbot.settings(key,value) VALUES('bot_replies_enabled',%s)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (json.dumps(enabled),),
        )
        if not enabled:
            db.execute(
                """UPDATE chatbot.whatsapp_inbox SET status='skipped',updated_at=%s
                WHERE status IN ('queued','generating')""", (now(),),
            )
    return {"bot_replies_enabled": enabled}


def ignore_whatsapp_attention(session, items):
    with _connection("administration") as db:
        return db.execute(
            """UPDATE chatbot.whatsapp_inbox AS inbox SET ignored_at=CURRENT_TIMESTAMP
            FROM jsonb_to_recordset(%s::jsonb) AS item(message_id text,updated_at text)
            WHERE inbox.session=%s AND inbox.message_id=item.message_id
              AND inbox.updated_at=item.updated_at AND inbox.ignored_at IS NULL
              AND inbox.status IN ('failed','uncertain')""",
            (json.dumps(items), session),
        ).rowcount


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


_VERSION_SUMMARY = """SELECT id,namespace,status,created_at,manifest,error,
    COALESCE((manifest::json->>'chunk_count')::integer,
             json_array_length(records::json)) AS chunk_count FROM chatbot.versions"""

_JOB_EXECUTION = """(SELECT jsonb_build_object(
    'environment',w.environment,
    'lease_active',COALESCE(w.lease_until>now(),false),
    'stalled',chatbot.jobs.status IN ('queued','running') AND
        CASE WHEN w.lease_until IS NOT NULL THEN w.lease_until<now()
        ELSE w.updated_at<now()-interval '5 minutes' END)
    FROM chatbot.admin_work w WHERE w.job_id=chatbot.jobs.id)"""

_JOB_SUMMARY = f"""SELECT id,kind,status,payload,progress,error,created_at,updated_at,
    {_JOB_EXECUTION} AS execution,
    EXISTS(SELECT 1 FROM chatbot.admin_work w WHERE w.job_id=chatbot.jobs.id
        AND chatbot.jobs.status<>'completed') AS resumable,
    (SELECT dispatch_error FROM chatbot.admin_work w WHERE w.job_id=chatbot.jobs.id) AS dispatch_error,
    result IS NOT NULL AS has_result,
    CASE WHEN json_typeof(result::json->'cases')='array'
         THEN json_array_length(result::json->'cases') END AS result_case_count
    FROM chatbot.jobs"""


_VERSION_JSON = "to_jsonb(item) || jsonb_build_object('manifest',item.manifest::jsonb)"
_JOB_JSON = """to_jsonb(item) || jsonb_build_object(
    'payload',item.payload::jsonb,'progress',item.progress::jsonb,
    'status',CASE WHEN item.status IN ('queued','running') AND
        COALESCE((item.execution->>'stalled')::boolean,false)
        THEN 'interrupted' ELSE item.status END,
    'dispatch_error',COALESCE(item.dispatch_error,
        CASE WHEN item.status IN ('queued','running') AND
            COALESCE((item.execution->>'stalled')::boolean,false)
        THEN 'Execution stopped (' || (item.execution->>'environment') || '). Resume saved work; completed cases are retained.' END))"""
_CONVERSATION_JSON = """to_jsonb(item) || jsonb_build_object(
    'usage',COALESCE(NULLIF(item.usage,'')::jsonb,'{}'::jsonb))"""
_PUBLISHED = "(SELECT value::jsonb FROM chatbot.settings WHERE key='published_version')"
_KNOWLEDGE_CATALOG = f"""SELECT to_jsonb(state) || jsonb_build_object(
    'sources',(SELECT COALESCE(jsonb_agg(to_jsonb(source)),'[]'::jsonb) FROM (
        SELECT s.id,s.name,s.enabled,s.updated_at,b.format,b.size_bytes,b.sha256,
        jsonb_array_length(b.pages) AS page_count FROM chatbot.knowledge_sources s
        JOIN chatbot.knowledge_blobs b ON b.id=s.blob_id
        WHERE s.deleted_at IS NULL ORDER BY lower(s.name)) source),
    'active',(SELECT {_VERSION_JSON} FROM ({_VERSION_SUMMARY} WHERE id=({_PUBLISHED} #>> '{{}}')) item),
    'active_expected',({_PUBLISHED} IS NOT NULL),
    'pending',state.revision<>state.applied_revision) AS data
    FROM chatbot.knowledge_state state WHERE state.id=1"""
_WHATSAPP_JSON = """jsonb_build_object(
    'bot_replies_enabled',COALESCE((SELECT value::jsonb FROM chatbot.settings
        WHERE key='bot_replies_enabled'),'true'::jsonb),
    'queue',(SELECT COALESCE(jsonb_object_agg(status,n),'{}'::jsonb) FROM (
        SELECT status,count(*) AS n FROM chatbot.whatsapp_inbox
        WHERE session=%(session)s GROUP BY status) counts),
    'attention',(SELECT jsonb_build_object(
        'failed',count(*) FILTER (WHERE status='failed'),
        'uncertain',count(*) FILTER (WHERE status='uncertain'),
        'items',COALESCE(jsonb_agg(jsonb_build_object(
            'message_id',message_id,'updated_at',updated_at)),'[]'::jsonb))
        FROM (SELECT message_id,updated_at,status FROM chatbot.whatsapp_inbox
            WHERE session=%(session)s AND status IN ('failed','uncertain') AND ignored_at IS NULL
            ORDER BY created_at,message_id LIMIT 1000) attention),
    'last_received_at',(SELECT MAX(created_at) FROM chatbot.whatsapp_inbox WHERE session=%(session)s),
    'last_sent_at',(SELECT MAX(updated_at) FROM chatbot.whatsapp_inbox WHERE session=%(session)s AND status='sent'),
    'last_ack_at',(SELECT MAX(updated_at) FROM chatbot.whatsapp_receipts))"""

_LATEST_QA = """(SELECT jsonb_build_object(
    'job_id',id,'created_at',created_at,
    'completed_at',result::jsonb->>'completed_at',
    'dataset',result::jsonb->>'dataset',
    'knowledge_version',result::jsonb->>'knowledge_version',
    'runtime_top_k',result::jsonb->'runtime_top_k',
    'averages',result::jsonb->'averages',
    'case_count',jsonb_array_length(result::jsonb->'cases'),
    'scored_cases',(SELECT COALESCE(jsonb_object_agg(name,n),'{}'::jsonb) FROM (
        SELECT metric->>'name' AS name,
            count(*) FILTER (WHERE jsonb_typeof(metric->'score')='number') AS n
        FROM jsonb_array_elements(result::jsonb->'cases') c,
            jsonb_array_elements(c->'metrics') metric
        GROUP BY metric->>'name') counts))
    FROM chatbot.jobs WHERE kind='evaluate' AND status='completed'
        AND result::jsonb->>'dataset' IN ('legacy','audited')
        AND jsonb_typeof(result::jsonb->'cases')='array'
    ORDER BY COALESCE((result::jsonb->>'completed_at')::timestamptz,
        created_at::timestamptz) DESC,created_at DESC,id DESC LIMIT 1)"""

_ADMIN_READS = {
    "me": "'{}'::jsonb",
    "whatsapp": _WHATSAPP_JSON,
    "knowledge": f"({_KNOWLEDGE_CATALOG})",
    "versions": f"""jsonb_build_object('published',{_PUBLISHED},'versions',
        (SELECT COALESCE(jsonb_agg({_VERSION_JSON}),'[]'::jsonb)
         FROM ({_VERSION_SUMMARY} ORDER BY created_at DESC) item))""",
    "settings": """(SELECT COALESCE(jsonb_object_agg(key,value::jsonb),'{}'::jsonb)
        FROM chatbot.settings WHERE key IN ('openrouter_model','eval_model','semantic_top_k'))""",
    "conversations": f"""(SELECT COALESCE(jsonb_agg({_CONVERSATION_JSON}),'[]'::jsonb)
        FROM (SELECT * FROM chatbot.conversations
              WHERE (%(channel)s::text IS NULL OR channel=%(channel)s)
              ORDER BY id DESC LIMIT 200) item)""",
    "jobs": f"""(SELECT COALESCE(jsonb_agg({_JOB_JSON}),'[]'::jsonb)
        FROM ({_JOB_SUMMARY} ORDER BY created_at DESC LIMIT 100) item)""",
    "job": f"""(SELECT {_JOB_JSON} || jsonb_build_object('result',item.result::jsonb)
        FROM (SELECT chatbot.jobs.*, {_JOB_EXECUTION} AS execution,
            EXISTS(SELECT 1 FROM chatbot.admin_work w WHERE w.job_id=chatbot.jobs.id
        AND chatbot.jobs.status<>'completed') AS resumable,
            (SELECT dispatch_error FROM chatbot.admin_work w WHERE w.job_id=chatbot.jobs.id) AS dispatch_error
            FROM chatbot.jobs WHERE id=%(job_id)s) item)""",
    "overview": f"""jsonb_build_object(
        'latest_evaluation',{_LATEST_QA},
        'conversations',(SELECT count(*) FROM chatbot.conversations),
        'whatsapp_messages',(SELECT count(*) FROM chatbot.conversations WHERE channel='whatsapp'),
        'average_latency',(SELECT round(avg(NULLIF(latency,0))::numeric,2) FROM chatbot.conversations),
        'recent',(SELECT COALESCE(jsonb_agg({_CONVERSATION_JSON}),'[]'::jsonb)
            FROM (SELECT * FROM chatbot.conversations ORDER BY id DESC LIMIT 8) item),
        'published',(SELECT {_VERSION_JSON} FROM ({_VERSION_SUMMARY}
            WHERE id=({_PUBLISHED} #>> '{{}}')) item),
        'jobs',(SELECT COALESCE(jsonb_agg({_JOB_JSON}),'[]'::jsonb)
            FROM ({_JOB_SUMMARY} ORDER BY created_at DESC LIMIT 8) item))""",
}


def admin_snapshot(token_hash, at, view, channel=None, job_id=None, session=None):
    """Authenticate and read one snapshot using the pooler's simple query protocol."""
    expression = _ADMIN_READS[view]
    open_pool()
    started = time.perf_counter()
    phase = "acquire"
    try:
        with _pool.connection() as db:
            acquired = time.perf_counter()
            phase = "snapshot"
            cursor = db.execute(
                "BEGIN READ ONLY; " + _TRANSACTION_SETUP + ";"
                "WITH valid_session AS MATERIALIZED (SELECT csrf FROM chatbot.sessions "
                "WHERE token_hash=%(token_hash)s AND expires>%(at)s) "
                "SELECT csrf," + expression + " AS data FROM valid_session; COMMIT",
                {"token_hash": token_hash, "at": at, "channel": channel, "job_id": job_id, "session": session},
            )
            for _ in range(4):
                cursor.nextset()
            row = cursor.fetchone()
        db._admin_last_used = time.monotonic()
    except (psycopg.Error, PoolTimeout) as error:
        logging.getLogger(__name__).warning(
            "Database failure phase=%s error=%s sqlstate=%s elapsed_ms=%.1f pool=%s",
            phase, type(error).__name__, error.sqlstate,
            (time.perf_counter() - started) * 1000, pool_stats(),
        )
        raise StateUnavailable(
            "Administration database is unavailable; inspect the private backend log."
        ) from None
    if row is not None:
        row["timing"] = {
            "db_acquire": (acquired - started) * 1000,
            "db_read": (time.perf_counter() - acquired) * 1000,
        }
    return row


def pool_stats():
    return _pool.get_stats() if _pool is not None else {}


def backfill_version_counts():
    with _connection("administration") as db:
        return db.execute(
            """UPDATE chatbot.versions SET manifest=jsonb_set(manifest::jsonb,
            '{chunk_count}',to_jsonb(json_array_length(records::json)))::text
            WHERE manifest::jsonb->'chunk_count' IS DISTINCT FROM
                to_jsonb(json_array_length(records::json))"""
        ).rowcount


def version(version_id=None):
    version_id = version_id or get_setting("published_version")
    with _connection() as db:
        row = db.execute(
            "SELECT * FROM chatbot.versions WHERE id=%s", (version_id,)
        ).fetchone()
    if not row:
        raise ValueError("Knowledge version not found.")
    return decode_version(row)


def version_info(version_id=None, *, namespace=None):
    column, value = ("namespace", namespace) if namespace else (
        "id", version_id or get_setting("published_version")
    )
    with _connection() as db:
        row = db.execute(_VERSION_SUMMARY + f" WHERE {column}=%s", (value,)).fetchone()
    if not row:
        raise ValueError("Knowledge version not found.")
    return dict(row, manifest=json.loads(row["manifest"]))


def save_version(item):
    records = item["records"]
    if (item["manifest"].get("embedding") or {}).get("provider") == "openrouter":
        # Remote vectors belong in Pinecone; duplicating them makes state transfers enormous.
        records = [{key: value for key, value in record.items() if key != "embedding"} for record in records]
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
                json.dumps(dict(item["manifest"], chunk_count=len(item["records"]))),
                json.dumps(records),
                item.get("error"),
            ),
        )


def publish(version_id):
    with _connection("administration", exclusive=True) as db:
        row = db.execute(
            "SELECT status,manifest FROM chatbot.versions WHERE id=%s FOR UPDATE", (version_id,)
        ).fetchone()
        if not row or row["status"] not in ("ready", "published"):
            raise ValueError("Only fully indexed, ready versions can be published.")
        from app.backend.vectorstore import require_compatible_version
        require_compatible_version({"manifest": json.loads(row["manifest"])})
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


def prompt_turns(session_id, channel=None):
    boundary = get_setting("reset:" + session_id, 0)
    with _connection() as db:
        rows = db.execute(
            """SELECT question,answer FROM chatbot.conversations
            WHERE session_id=%s AND id>%s AND answer<>''
            AND (%s::text IS NULL OR channel=%s) ORDER BY id DESC LIMIT 8""",
            (session_id, boundary, channel, channel),
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
    return [_decode_job(row) for row in rows]


def _decode_job(row):
    item = dict(
        row, payload=json.loads(row["payload"]), progress=json.loads(row["progress"])
    )
    if "result" in item:
        item["result"] = json.loads(item["result"]) if item["result"] else None
    return item


def job(identifier):
    with _connection() as db:
        row = db.execute(
            "SELECT * FROM chatbot.jobs WHERE id=%s", (identifier,)
        ).fetchone()
    return _decode_job(row) if row else None


def evaluation_result(identifier):
    with _connection() as db:
        row = db.execute(
            """SELECT result FROM chatbot.jobs WHERE kind='evaluate'
            AND result::jsonb->>'id'=%s ORDER BY created_at DESC LIMIT 1""",
            (identifier,),
        ).fetchone()
    return json.loads(row["result"]) if row else None


def save_evaluation_result(identifier, result):
    with _connection("execution") as db:
        db.execute(
            """UPDATE chatbot.jobs SET result=%s,updated_at=%s
            WHERE kind='evaluate' AND result::jsonb->>'id'=%s""",
            (json.dumps(result), now(), identifier),
        )


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
    status = "queued" if _bot_replies_enabled(db) else "skipped"
    inserted = db.execute(
        """INSERT INTO chatbot.whatsapp_inbox(session,message_id,sender,body,status,reply_ids,created_at,updated_at)
        VALUES(%s,%s,%s,%s,%s,'[]',%s,%s) ON CONFLICT(session,message_id) DO NOTHING""",
        (session, message_id, sender, body, status, received_at or now(), now()),
    ).rowcount
    if not inserted:
        row = db.execute(
            "SELECT sender,body FROM chatbot.whatsapp_inbox WHERE session=%s AND message_id=%s",
            (session,message_id),
        ).fetchone()
        if row["sender"] != sender or row["body"] != body:
            raise ValueError("Duplicate WhatsApp ID has conflicting content; review before replay.")
    elif status == "skipped":
        db.execute(
            """INSERT INTO chatbot.conversations(session_id,channel,question,answer,usage,latency,created_at)
            VALUES(%s,'whatsapp',%s,'','{}',0,%s)""",
            ("wa_" + sender.removesuffix("@c.us"), body, received_at or now()),
        )
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


def claim_inbox(session, message_id=None):
    with _connection("execution") as db:
        target = db.execute(
            """SELECT * FROM chatbot.whatsapp_inbox WHERE session=%s
            AND (%s::text IS NULL OR message_id=%s) AND status IN ('queued','generating','sending')
            ORDER BY created_at,message_id LIMIT 1""", (session, message_id, message_id),
        ).fetchone()
        if not target or not db.execute(
            "SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS acquired",
            ("whatsapp:" + session + ":" + target["sender"],),
        ).fetchone()["acquired"]:
            return None
        # Expired sends have an unknown outcome. Never retry them automatically.
        db.execute(
            """UPDATE chatbot.whatsapp_inbox SET status=CASE WHEN status='sending' THEN 'uncertain' ELSE 'failed' END,
            error='Execution expired; inspect the message before retrying.',updated_at=%s,
            delivery_parts=CASE WHEN status='sending' THEN
              (SELECT COALESCE(jsonb_object_agg(key,CASE WHEN value->>'status'='sending'
                THEN value || '{"status":"uncertain"}'::jsonb ELSE value END),'{}'::jsonb)
               FROM jsonb_each(delivery_parts)) ELSE delivery_parts END
            WHERE session=%s AND sender=%s AND (
              (status='sending' AND COALESCE(lease_expires_at,updated_at::timestamptz+interval '5 minutes')<CURRENT_TIMESTAMP)
              OR (status='generating' AND lease_token IS NULL AND updated_at::timestamptz<CURRENT_TIMESTAMP-interval '5 minutes')
              OR (status='queued' AND created_at::timestamptz<CURRENT_TIMESTAMP-interval '15 minutes'))""",
            (now(), session, target["sender"]),
        )
        return db.execute(
            """UPDATE chatbot.whatsapp_inbox AS pending SET status='generating',updated_at=%s,
            lease_token=%s,lease_expires_at=CURRENT_TIMESTAMP+interval '5 minutes',
            generation_started_at=COALESCE(generation_started_at,CURRENT_TIMESTAMP)
            WHERE session=%s AND message_id=%s
            AND (status='queued' OR (status='generating' AND lease_token IS NOT NULL AND lease_expires_at<CURRENT_TIMESTAMP))
            AND NOT EXISTS(SELECT 1 FROM chatbot.whatsapp_inbox AS earlier
                WHERE earlier.session=pending.session AND earlier.sender=pending.sender
                AND earlier.status IN ('queued','generating','sending') AND earlier.message_id<>pending.message_id
                AND (earlier.created_at,earlier.message_id)<(pending.created_at,pending.message_id))
            RETURNING pending.*""", (now(), uuid.uuid4().hex, session, target["message_id"]),
        ).fetchone()


def begin_inbox_send(session, message_id, lease_token=None):
    with _connection("execution") as db:
        if not _bot_replies_enabled(db):
            return False
        return bool(db.execute(
            """UPDATE chatbot.whatsapp_inbox SET status='sending',updated_at=%s,send_started_at=CURRENT_TIMESTAMP
            WHERE session=%s AND message_id=%s AND status='generating'
            AND (%s::text IS NULL OR (lease_token=%s AND lease_expires_at>CURRENT_TIMESTAMP))""",
            (now(), session, message_id, lease_token, lease_token),
        ).rowcount)


def update_inbox(session, message_id, fields, lease_token=None):
    from psycopg import sql

    allowed = {"status", "answer", "media_url", "reply_ids", "error", "media_selection",
               "delivery_parts", "media_conversation_key", "media_epoch", "media_focus"}
    if not fields or not set(fields) <= allowed:
        raise ValueError("Invalid inbox update fields.")
    if "status" in fields and fields["status"] not in (
        "queued",
        "generating",
        "sending",
        "sent",
        "failed",
        "uncertain",
        "skipped",
    ):
        raise ValueError("Invalid inbox state.")
    from psycopg.types.json import Jsonb
    values = dict(fields, updated_at=now())
    media_focus = values.pop('media_focus', None)
    for key in ("media_selection", "delivery_parts"):
        if key in values and values[key] is not None:
            values[key] = Jsonb(values[key])
    if fields.get("answer") is not None:
        values["generated_at"] = now()
    if fields.get("status") == "sent":
        values["sent_at"] = now()
    assignments = sql.SQL(",").join(
        sql.SQL("{}=%s").format(sql.Identifier(k)) for k in values
    )
    with _connection("execution") as db:
        result = db.execute(
            sql.SQL(
                "UPDATE chatbot.whatsapp_inbox SET {} WHERE session=%s AND message_id=%s AND status<>'skipped' "
                "AND (%s::text IS NULL OR lease_token=%s)"
            ).format(assignments),
            (*values.values(), session, message_id, lease_token, lease_token),
        )
        if result.rowcount and media_focus is not None:
            db.execute('UPDATE chatbot.catalog_conversations SET focus=%s WHERE conversation_key=%s AND epoch=%s',
                       (Jsonb(media_focus),fields.get('media_conversation_key'),fields.get('media_epoch')))


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
        data = db.execute("SELECT " + _WHATSAPP_JSON + " AS data", {"session": session}).fetchone()["data"]
    return dict(data, checked_at=now())


def catalog_snapshot():
    with _connection() as db:
        return db.execute("""SELECT jsonb_build_object('revision',s.revision,'enabled',s.enabled,
            'assets',COALESCE((SELECT jsonb_agg(a.metadata || jsonb_build_object(
            'asset_id',a.asset_id,'revision',a.revision,'enabled',a.enabled,
            'approved_by',a.approved_by,'updated_at',a.updated_at) ORDER BY a.asset_id)
            FROM chatbot.catalog_assets a),'[]'::jsonb)) AS data
            FROM chatbot.catalog_state s WHERE id=1""").fetchone()['data']


def save_catalog_asset(data, expected_revision, approved_by):
    from app.admin.catalog import Conflict
    from psycopg.types.json import Jsonb
    with _connection('administration') as db:
        db.execute('SELECT revision FROM chatbot.catalog_state WHERE id=1 FOR UPDATE')
        old = db.execute('SELECT revision FROM chatbot.catalog_assets WHERE asset_id=%s',
                         (data['asset_id'],)).fetchone()
        if (old['revision'] if old else 0) != expected_revision:
            raise Conflict('This image changed. Reload before saving again.')
        revision = expected_revision + 1
        db.execute('''INSERT INTO chatbot.catalog_assets(asset_id,revision,enabled,metadata,approved_by)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(asset_id) DO UPDATE SET
            revision=excluded.revision,enabled=excluded.enabled,metadata=excluded.metadata,
            approved_by=excluded.approved_by,updated_at=now()''',
            (data['asset_id'],revision,data['enabled'],Jsonb(data),approved_by))
        db.execute('UPDATE chatbot.catalog_state SET revision=revision+1 WHERE id=1')
        return {**data, 'revision': revision, 'approved_by': approved_by}


def catalog_asset_enabled(asset_id):
    with _connection() as db:
        row = db.execute('SELECT enabled FROM chatbot.catalog_assets WHERE asset_id=%s', (asset_id,)).fetchone()
        return bool(row and row['enabled'])


def catalog_feature(enabled):
    with _connection('administration') as db:
        db.execute('UPDATE chatbot.catalog_state SET enabled=%s,revision=revision+1 WHERE id=1', (enabled,))


def catalog_stage_upload(identifier, object_key, size_bytes):
    with _connection('administration') as db:
        db.execute('INSERT INTO chatbot.catalog_uploads(id,object_key,size_bytes) VALUES(%s,%s,%s)',
                   (identifier,object_key,size_bytes))


def catalog_upload(identifier):
    with _connection() as db:
        row = db.execute('SELECT * FROM chatbot.catalog_uploads WHERE id=%s AND expires_at>now()',
                         (identifier,)).fetchone()
        if not row:
            raise ValueError('Image upload expired or was not found. Upload again.')
        return row


def catalog_context(conversation_key, *, reset=False):
    from psycopg.types.json import Jsonb
    with _connection('execution') as db:
        db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('catalog:' + conversation_key,))
        row = db.execute('SELECT *,last_activity<now()-interval \'24 hours\' AS expired FROM chatbot.catalog_conversations WHERE conversation_key=%s FOR UPDATE',
                         (conversation_key,)).fetchone()
        fresh = reset or not row or row['expired']
        epoch = uuid.uuid4().hex if fresh else row['epoch']
        focus = [] if fresh else row['focus']
        preview_seen = [] if fresh else row['preview_seen']
        db.execute('''INSERT INTO chatbot.catalog_conversations(conversation_key,epoch,focus,preview_seen)
            VALUES(%s,%s,%s,%s) ON CONFLICT(conversation_key) DO UPDATE SET
            epoch=excluded.epoch,focus=excluded.focus,preview_seen=excluded.preview_seen,last_activity=now()''',
            (conversation_key,epoch,Jsonb(focus),Jsonb(preview_seen)))
        rows = db.execute('''SELECT media_selection FROM chatbot.whatsapp_inbox
            WHERE media_conversation_key=%s AND media_epoch=%s AND
            (delivery_parts->'image'->>'status') IN ('sending','sent','uncertain')''',
            (conversation_key,epoch)).fetchall()
        return {'key': conversation_key, 'epoch': epoch, 'focus': focus,
                'seen': preview_seen + [r['media_selection']['asset_id'] for r in rows if r['media_selection']], 'fresh': fresh}


def catalog_focus(context, focus, *, preview_asset=None):
    from psycopg.types.json import Jsonb
    with _connection('execution') as db:
        row = db.execute('SELECT preview_seen FROM chatbot.catalog_conversations WHERE conversation_key=%s AND epoch=%s FOR UPDATE',
                         (context['key'],context['epoch'])).fetchone()
        if not row:
            return
        seen = row['preview_seen']
        if preview_asset and preview_asset['asset_id'] not in seen:
            seen.append(preview_asset['asset_id'])
        db.execute('UPDATE chatbot.catalog_conversations SET focus=%s,preview_seen=%s WHERE conversation_key=%s AND epoch=%s',
                   (Jsonb(focus),Jsonb(seen),context['key'],context['epoch']))


def checkpoint_delivery_part(row, part, state, *, provider_id=None, error=None):
    from psycopg.types.json import Jsonb
    with _connection('execution') as db:
        current = db.execute('''SELECT * FROM chatbot.whatsapp_inbox WHERE session=%s AND message_id=%s
            AND status<>'skipped' AND (%s::text IS NULL OR (lease_token=%s AND lease_expires_at>now())) FOR UPDATE''',
            (row['session'],row['message_id'],row.get('lease_token'),row.get('lease_token'))).fetchone()
        if not current:
            raise StateUnavailable('Delivery execution lease was lost.')
        previous = current['delivery_parts'].get(part, {})
        if previous.get('status') in ('sent','uncertain','sending') and state == 'sending':
            raise StateUnavailable('A submitted delivery part must not be sent again.')
        if state == 'sending' and not _bot_replies_enabled(db):
            return False
        if state == 'sending' and part == 'image' and current['media_selection']:
            asset = db.execute('SELECT enabled FROM chatbot.catalog_assets WHERE asset_id=%s',
                               (current['media_selection']['asset_id'],)).fetchone()
            feature = db.execute('SELECT enabled FROM chatbot.catalog_state WHERE id=1').fetchone()
            if not feature['enabled'] or not asset or not asset['enabled']:
                return False
        value = {'status': state, 'provider_id': provider_id, 'error': error}
        parts = {**current['delivery_parts'], part: value}
        replies = [p['provider_id'] for p in parts.values() if p.get('provider_id')]
        db.execute('UPDATE chatbot.whatsapp_inbox SET delivery_parts=%s,reply_ids=%s,updated_at=%s WHERE session=%s AND message_id=%s',
                   (Jsonb(parts),json.dumps(replies),now(),row['session'],row['message_id']))
        row['delivery_parts'] = parts
        row['reply_ids'] = json.dumps(replies)
        return True
