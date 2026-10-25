CREATE TABLE chatbot.knowledge_state (
    id integer PRIMARY KEY CHECK (id=1),
    revision bigint NOT NULL DEFAULT 0,
    applied_revision bigint NOT NULL DEFAULT -1,
    chunking jsonb NOT NULL DEFAULT '{"chunk_size":1000,"chunk_overlap":100,"preprocessing":"sections-v1"}',
    sync_job text REFERENCES chatbot.jobs(id),
    initialized boolean NOT NULL DEFAULT false
);
INSERT INTO chatbot.knowledge_state(id,chunking)
SELECT 1,COALESCE((SELECT manifest::jsonb->'chunking' FROM chatbot.versions
WHERE id=(SELECT value::jsonb#>>'{}' FROM chatbot.settings WHERE key='published_version')),
CASE WHEN EXISTS(SELECT 1 FROM chatbot.settings WHERE key='published_version')
THEN '{"chunk_size":1500,"chunk_overlap":200,"preprocessing":"legacy"}'::jsonb
ELSE '{"chunk_size":1000,"chunk_overlap":100,"preprocessing":"sections-v1"}'::jsonb END);
CREATE TABLE chatbot.knowledge_blobs (
    id text PRIMARY KEY,
    object_path text NOT NULL UNIQUE,
    name text NOT NULL,
    format text NOT NULL CHECK (format IN ('txt','pdf')),
    size_bytes integer NOT NULL CHECK (size_bytes BETWEEN 1 AND 10485760),
    sha256 text,
    pages jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    removed_at timestamptz
);
CREATE TABLE chatbot.knowledge_sources (
    id text PRIMARY KEY,
    name text NOT NULL,
    blob_id text NOT NULL REFERENCES chatbot.knowledge_blobs(id),
    enabled boolean NOT NULL DEFAULT true,
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);
CREATE UNIQUE INDEX knowledge_sources_name ON chatbot.knowledge_sources(lower(name)) WHERE deleted_at IS NULL;
CREATE INDEX knowledge_sources_blob ON chatbot.knowledge_sources(blob_id);
CREATE TABLE chatbot.admin_work (
    job_id text PRIMARY KEY REFERENCES chatbot.jobs(id),
    environment text NOT NULL,
    checkpoint jsonb NOT NULL DEFAULT '{}',
    sequence bigint NOT NULL DEFAULT 0,
    attempts integer NOT NULL DEFAULT 0,
    lease_token text,
    lease_until timestamptz,
    dispatch_error text,
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE chatbot.versions ADD COLUMN retired_at timestamptz;
ALTER TABLE chatbot.versions ADD COLUMN vectors_removed_at timestamptz;
UPDATE chatbot.knowledge_state SET initialized=true
WHERE NOT EXISTS(SELECT 1 FROM chatbot.settings WHERE key='published_version');
UPDATE chatbot.versions SET retired_at=now() WHERE status<>'published';
DO $policies$
DECLARE name text;
BEGIN
    FOREACH name IN ARRAY ARRAY['knowledge_state','knowledge_blobs','knowledge_sources','admin_work'] LOOP
        EXECUTE format('ALTER TABLE chatbot.%I ENABLE ROW LEVEL SECURITY',name);
        EXECUTE format('ALTER TABLE chatbot.%I FORCE ROW LEVEL SECURITY',name);
        EXECUTE format('REVOKE ALL ON chatbot.%I FROM PUBLIC,anon,authenticated',name);
        EXECUTE format('GRANT SELECT,INSERT,UPDATE ON chatbot.%I TO chatbot_app',name);
        EXECUTE format('CREATE POLICY backend_access ON chatbot.%I TO chatbot_app USING (true) WITH CHECK (true)',name);
    END LOOP;
END $policies$;
