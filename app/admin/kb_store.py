"""Global source configuration and fenced, checkpointed administration work."""

import json
import os
import uuid

from psycopg.types.json import Jsonb

from app.admin import store


def environment():
    if os.getenv("VERCEL") == "1":
        env = os.getenv("VERCEL_ENV", "preview")
        return (
            "production"
            if env == "production"
            else "preview:" + os.getenv("VERCEL_DEPLOYMENT_ID", "unknown")
        )
    return "local"


def _state(db, editable=False):
    state = db.execute(
        "SELECT * FROM chatbot.knowledge_state WHERE id=1 FOR UPDATE"
    ).fetchone()
    if editable and state["sync_job"]:
        raise ValueError(
            "Knowledge synchronization is running; source changes are locked."
        )
    return state


def catalog():
    with store._connection() as db:
        data = db.execute(store._KNOWLEDGE_CATALOG).fetchone()["data"]
    return validate_catalog(data)


def validate_catalog(data):
    if not data or (data["active_expected"] and data["active"] is None):
        raise store.StateUnavailable("Active knowledge selection is inconsistent.")
    return data


def active_info():
    try:
        return store.version_info()
    except ValueError:
        if store.get_setting("published_version"):
            raise store.StateUnavailable(
                "Active knowledge selection is inconsistent."
            ) from None
        return None


def stage_upload(name, size, source_id=None):
    identifier = uuid.uuid4().hex
    with store._connection("administration") as db:
        _state(db, editable=True)
        if (
            source_id
            and not db.execute(
                "SELECT 1 FROM chatbot.knowledge_sources WHERE id=%s AND deleted_at IS NULL",
                (source_id,),
            ).fetchone()
        ):
            raise ValueError("Source not found.")
        db.execute(
            """INSERT INTO chatbot.knowledge_blobs(id,object_path,name,format,size_bytes)
          VALUES(%s,%s,%s,%s,%s)""",
            (
                identifier,
                "sources/" + identifier + "/" + name,
                name,
                name.rsplit(".", 1)[-1],
                size,
            ),
        )
    return identifier


def blob(identifier):
    with store._connection() as db:
        row = db.execute(
            "SELECT * FROM chatbot.knowledge_blobs WHERE id=%s AND removed_at IS NULL",
            (identifier,),
        ).fetchone()
    if not row:
        raise ValueError("Upload not found.")
    return row


def source(identifier):
    with store._connection() as db:
        row = db.execute(
            """SELECT b.*,s.id AS source_id,s.enabled FROM chatbot.knowledge_sources s
          JOIN chatbot.knowledge_blobs b ON b.id=s.blob_id WHERE s.id=%s AND s.deleted_at IS NULL""",
            (identifier,),
        ).fetchone()
    if not row:
        raise ValueError("Source not found.")
    return row


def finish_upload(identifier, digest, pages, source_id=None):
    with store._connection("administration") as db:
        _state(db, editable=True)
        upload = db.execute(
            "SELECT * FROM chatbot.knowledge_blobs WHERE id=%s AND removed_at IS NULL FOR UPDATE",
            (identifier,),
        ).fetchone()
        if not upload:
            raise ValueError("Upload not found.")
        existing = db.execute(
            "SELECT id FROM chatbot.knowledge_sources WHERE blob_id=%s AND deleted_at IS NULL",
            (identifier,),
        ).fetchone()
        if existing:
            return existing["id"]
        if db.execute(
            """SELECT 1 FROM chatbot.knowledge_sources s JOIN chatbot.knowledge_blobs b ON b.id=s.blob_id
          WHERE s.deleted_at IS NULL AND (%s::text IS NULL OR s.id<>%s) AND (lower(s.name)=lower(%s) OR b.sha256=%s)""",
            (source_id, source_id, upload["name"], digest),
        ).fetchone():
            raise ValueError(
                "A source with this name or identical file already exists. Use Replace on that source."
            )
        db.execute(
            "UPDATE chatbot.knowledge_blobs SET sha256=%s,pages=%s WHERE id=%s",
            (digest, Jsonb(pages), identifier),
        )
        if source_id:
            changed = db.execute(
                """UPDATE chatbot.knowledge_sources SET blob_id=%s,name=%s,updated_at=now()
              WHERE id=%s AND deleted_at IS NULL""",
                (identifier, upload["name"], source_id),
            ).rowcount
            if not changed:
                raise ValueError("Source not found.")
        else:
            source_id = uuid.uuid4().hex
            db.execute(
                "INSERT INTO chatbot.knowledge_sources(id,name,blob_id) VALUES(%s,%s,%s)",
                (source_id, upload["name"], identifier),
            )
        db.execute("UPDATE chatbot.knowledge_state SET revision=revision+1 WHERE id=1")
    return source_id


def change_source(identifier, *, enabled=None, delete=False):
    with store._connection("administration") as db:
        _state(db, editable=True)
        row = db.execute(
            "SELECT * FROM chatbot.knowledge_sources WHERE id=%s AND deleted_at IS NULL",
            (identifier,),
        ).fetchone()
        if not row:
            raise ValueError("Source not found.")
        if delete:
            db.execute(
                "UPDATE chatbot.knowledge_sources SET deleted_at=now(),updated_at=now() WHERE id=%s",
                (identifier,),
            )
        elif row["enabled"] != enabled:
            db.execute(
                "UPDATE chatbot.knowledge_sources SET enabled=%s,updated_at=now() WHERE id=%s",
                (enabled, identifier),
            )
        else:
            return
        db.execute("UPDATE chatbot.knowledge_state SET revision=revision+1 WHERE id=1")


def configure(chunking):
    with store._connection("administration") as db:
        _state(db, editable=True)
        db.execute(
            "UPDATE chatbot.knowledge_state SET chunking=%s,revision=revision+1 WHERE id=1",
            (Jsonb(chunking),),
        )


def _insert_job(db, identifier, kind, payload, checkpoint):
    db.execute(
        """INSERT INTO chatbot.jobs(id,kind,status,payload,created_at,updated_at)
      VALUES(%s,%s,'queued',%s,%s,%s)""",
        (identifier, kind, json.dumps(payload), store.now(), store.now()),
    )
    db.execute(
        "INSERT INTO chatbot.admin_work(job_id,environment,checkpoint) VALUES(%s,%s,%s)",
        (identifier, environment(), Jsonb(checkpoint)),
    )


def start_sync():
    from app.backend.models import embedding_identity
    from app.config.settings import get_settings

    identifier = uuid.uuid4().hex
    with store._connection("administration") as db:
        state = _state(db, editable=True)
        if not state["initialized"]:
            raise ValueError("Import current active sources before synchronizing.")
        size = db.execute("""SELECT COALESCE(sum(octet_length(b.pages::text)),0) AS bytes
          FROM chatbot.knowledge_sources s JOIN chatbot.knowledge_blobs b ON b.id=s.blob_id
          WHERE s.deleted_at IS NULL AND s.enabled""").fetchone()["bytes"]
        if size > 5_000_000:
            raise ValueError(
                "Active extracted knowledge exceeds 5 MB. Disable or shorten sources before syncing."
            )
        rows = db.execute("""SELECT s.id AS source_id,s.name,b.id AS blob_id,b.sha256,b.pages,b.format
          FROM chatbot.knowledge_sources s JOIN chatbot.knowledge_blobs b ON b.id=s.blob_id
          WHERE s.deleted_at IS NULL AND s.enabled ORDER BY s.name""").fetchall()
        _insert_job(
            db,
            identifier,
            "sync",
            {"revision": state["revision"]},
            {
                "phase": "prepare",
                "sources": rows,
                "chunking": state["chunking"],
                "revision": state["revision"],
                "embedding": embedding_identity(),
                "vector_index": get_settings().pinecone_index_name,
            },
        )
        db.execute(
            "UPDATE chatbot.knowledge_state SET sync_job=%s WHERE id=1", (identifier,)
        )
    return identifier


def create_evaluation(payload, checkpoint):
    identifier = uuid.uuid4().hex
    with store._connection("administration") as db:
        # Activation and submission use this same lock: pin one unambiguous active snapshot.
        _state(db)
        row = db.execute("""SELECT v.* FROM chatbot.versions v JOIN chatbot.settings s
          ON s.key='published_version' AND v.id=s.value::jsonb#>>'{}'""").fetchone()
        if not row or not json.loads(row["manifest"]).get(
            "chunk_count", len(json.loads(row["records"]))
        ):
            raise ValueError("Sync searchable knowledge before starting an evaluation.")
        item = store.decode_version(row)
        from app.backend.vectorstore import require_compatible_version

        require_compatible_version(item)
        payload = {**payload, "version_id": item["id"], "namespace": item["namespace"]}
        _insert_job(
            db,
            identifier,
            "evaluate",
            payload,
            {**checkpoint, "snapshot": item, "phase": "prepare"},
        )
    return identifier


def work(identifier):
    with store._connection() as db:
        return db.execute(
            """SELECT w.*,j.kind,j.status,j.payload,j.result,j.error FROM chatbot.admin_work w
          JOIN chatbot.jobs j ON j.id=w.job_id WHERE w.job_id=%s""",
            (identifier,),
        ).fetchone()


def claim(identifier, sequence):
    token = uuid.uuid4().hex
    with store._connection("execution") as db:
        _state(db)
        row = db.execute(
            """UPDATE chatbot.admin_work w SET lease_token=%s,lease_until=now()+interval '4 minutes',
          attempts=attempts+1 WHERE job_id=%s AND sequence=%s AND environment=%s
          AND (lease_until IS NULL OR lease_until<now())
          AND EXISTS(SELECT 1 FROM chatbot.jobs j WHERE j.id=w.job_id AND j.status IN ('queued','running')) RETURNING *""",
            (token, identifier, sequence, environment()),
        ).fetchone()
        if row:
            db.execute(
                "UPDATE chatbot.jobs SET status='running',updated_at=%s WHERE id=%s",
                (store.now(), identifier),
            )
    return row


def checkpoint(
    identifier, token, value, progress, *, result=None, error=None, done=False
):
    with store._connection("execution") as db:
        _state(db)
        row = db.execute(
            """UPDATE chatbot.admin_work SET checkpoint=%s,sequence=sequence+1,attempts=0,
          lease_token=NULL,lease_until=NULL,updated_at=now(),dispatch_error=NULL
          WHERE job_id=%s AND lease_token=%s AND lease_until>now() RETURNING job_id""",
            (Jsonb(value), identifier, token),
        ).fetchone()
        if not row:
            raise RuntimeError(
                "Administration execution lease expired; checkpoint rejected."
            )
        db.execute(
            "UPDATE chatbot.jobs SET status=%s,progress=%s,result=%s,error=%s,updated_at=%s WHERE id=%s",
            (
                "failed" if error else "completed" if done else "running",
                json.dumps(progress),
                json.dumps(result) if result is not None else None,
                error,
                store.now(),
                identifier,
            ),
        )
        if done or error:
            db.execute(
                "UPDATE chatbot.knowledge_state SET sync_job=NULL WHERE sync_job=%s",
                (identifier,),
            )


def release_error(identifier, token, error):
    with store._connection("execution") as db:
        _state(db)
        row = db.execute(
            """UPDATE chatbot.admin_work SET lease_token=NULL,lease_until=NULL,updated_at=now()
          WHERE job_id=%s AND lease_token=%s RETURNING attempts""",
            (identifier, token),
        ).fetchone()
        if row and row["attempts"] >= 3:
            db.execute(
                "UPDATE chatbot.jobs SET status='failed',error=%s,updated_at=%s WHERE id=%s",
                (error, store.now(), identifier),
            )
            db.execute(
                "UPDATE chatbot.versions SET retired_at=now() WHERE id=%s AND status<>'published'",
                ("kb-" + identifier,),
            )
            db.execute(
                "UPDATE chatbot.knowledge_state SET sync_job=NULL WHERE sync_job=%s",
                (identifier,),
            )


def retry(identifier):
    with store._connection("administration") as db:
        state = _state(db)
        row = db.execute(
            """SELECT j.kind,j.status,w.environment,w.lease_until>now() AS owned FROM chatbot.jobs j JOIN chatbot.admin_work w ON w.job_id=j.id
          WHERE j.id=%s FOR UPDATE""",
            (identifier,),
        ).fetchone()
        if (
            not row
            or row["environment"] != environment()
            or row["status"] == "completed"
        ):
            raise ValueError("This job cannot be resumed in this environment.")
        if row["owned"]:
            raise ValueError(
                "This step is still running. Resume is available after its execution lease expires."
            )
        if row["kind"] == "sync":
            if state["sync_job"] not in (None, identifier):
                raise ValueError("Another synchronization is running.")
            checkpoint = db.execute(
                "SELECT checkpoint FROM chatbot.admin_work WHERE job_id=%s",
                (identifier,),
            ).fetchone()["checkpoint"]
            if checkpoint["revision"] != state["revision"]:
                raise ValueError(
                    "Knowledge changed after this job failed. Start a new synchronization."
                )
            db.execute(
                "UPDATE chatbot.knowledge_state SET sync_job=%s WHERE id=1",
                (identifier,),
            )
        db.execute(
            "UPDATE chatbot.jobs SET status='queued',error=NULL,updated_at=%s WHERE id=%s",
            (store.now(), identifier),
        )
        db.execute(
            "UPDATE chatbot.admin_work SET attempts=0,sequence=sequence+1 WHERE job_id=%s",
            (identifier,),
        )


def activate(identifier, token, snapshot_id, revision):
    with store._connection("execution") as db:
        state = _state(db)
        lease = db.execute(
            "SELECT 1 FROM chatbot.admin_work WHERE job_id=%s AND lease_token=%s AND lease_until>now()",
            (identifier, token),
        ).fetchone()
        if (
            not lease
            or state["sync_job"] != identifier
            or state["revision"] != revision
        ):
            raise ValueError("Synchronization no longer owns this configuration.")
        db.execute(
            "UPDATE chatbot.versions SET status='ready',retired_at=now() WHERE status='published' AND id<>%s",
            (snapshot_id,),
        )
        db.execute(
            """UPDATE chatbot.versions SET status='published',retired_at=NULL,
            manifest=(manifest::jsonb||jsonb_build_object('synced_at',now()::text))::text WHERE id=%s""",
            (snapshot_id,),
        )
        db.execute(
            """INSERT INTO chatbot.settings(key,value) VALUES('published_version',%s)
          ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (json.dumps(snapshot_id),),
        )
        db.execute(
            "UPDATE chatbot.knowledge_state SET applied_revision=%s WHERE id=1",
            (revision,),
        )


def garbage_candidates(index_name):
    with store._connection() as db:
        snapshots = db.execute(
            """SELECT v.id,v.namespace FROM chatbot.versions v
          WHERE v.retired_at<now()-interval '24 hours' AND v.vectors_removed_at IS NULL AND v.status<>'published'
          AND v.manifest::jsonb->>'vector_index'=%s AND (v.namespace LIKE 'kb-%%' OR v.namespace LIKE 'avg-%%')
          AND NOT EXISTS(SELECT 1 FROM chatbot.jobs j WHERE j.kind='sync' AND v.id='kb-'||j.id AND
            (j.status IN ('queued','running') OR (j.status IN ('failed','interrupted')
             AND j.payload::jsonb->>'revision'=(SELECT revision::text FROM chatbot.knowledge_state WHERE id=1))))
          AND NOT EXISTS(SELECT 1 FROM chatbot.jobs j WHERE j.kind='evaluate' AND j.status IN ('queued','running','failed','interrupted')
            AND j.payload::jsonb->>'version_id'=v.id) LIMIT 1""",
            (index_name,),
        ).fetchall()
        blobs = db.execute("""SELECT b.id,b.object_path FROM chatbot.knowledge_blobs b
          WHERE (b.removed_at IS NULL OR b.pages IS NOT NULL) AND b.created_at<now()-interval '24 hours'
          AND NOT EXISTS(SELECT 1 FROM chatbot.knowledge_sources s WHERE s.blob_id=b.id AND s.deleted_at IS NULL)
          AND NOT EXISTS(SELECT 1 FROM chatbot.versions v WHERE v.vectors_removed_at IS NULL
            AND v.manifest::jsonb->'source_refs' @> jsonb_build_array(jsonb_build_object('blob_id',b.id))) LIMIT 1""").fetchall()
    return snapshots, blobs


def claim_blob_deletion(identifier):
    with store._connection("execution") as db:
        _state(db)
        return bool(
            db.execute(
                """UPDATE chatbot.knowledge_blobs b SET removed_at=now(),pages=COALESCE(pages,'[]'::jsonb)
          WHERE b.id=%s AND NOT EXISTS(SELECT 1 FROM chatbot.knowledge_sources s WHERE s.blob_id=b.id AND s.deleted_at IS NULL)
          AND NOT EXISTS(SELECT 1 FROM chatbot.versions v WHERE v.vectors_removed_at IS NULL
            AND v.manifest::jsonb->'source_refs' @> jsonb_build_array(jsonb_build_object('blob_id',b.id))) RETURNING b.id""",
                (identifier,),
            ).fetchone()
        )


def finish_deletion(*, snapshot_id=None, blob_id=None):
    with store._connection("execution") as db:
        if snapshot_id:
            db.execute(
                "UPDATE chatbot.versions SET vectors_removed_at=now() WHERE id=%s",
                (snapshot_id,),
            )
        if blob_id:
            db.execute(
                "UPDATE chatbot.knowledge_blobs SET pages=NULL WHERE id=%s AND removed_at IS NOT NULL",
                (blob_id,),
            )
