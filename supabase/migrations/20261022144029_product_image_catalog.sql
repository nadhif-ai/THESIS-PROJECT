CREATE TABLE chatbot.catalog_state (
    id integer PRIMARY KEY CHECK (id=1),
    revision bigint NOT NULL DEFAULT 0,
    enabled boolean NOT NULL DEFAULT false
);
INSERT INTO chatbot.catalog_state(id) VALUES(1);
CREATE TABLE chatbot.catalog_assets (
    asset_id text PRIMARY KEY,
    revision bigint NOT NULL DEFAULT 1,
    enabled boolean NOT NULL,
    metadata jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    approved_by text NOT NULL
);
CREATE TABLE chatbot.catalog_uploads (
    id text PRIMARY KEY,
    object_key text NOT NULL UNIQUE,
    size_bytes integer NOT NULL CHECK(size_bytes BETWEEN 1 AND 10485760),
    expires_at timestamptz NOT NULL DEFAULT now()+interval '1 hour'
);
CREATE TABLE chatbot.catalog_conversations (
    conversation_key text PRIMARY KEY,
    epoch text NOT NULL,
    focus jsonb NOT NULL DEFAULT '[]',
    last_activity timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE chatbot.whatsapp_inbox
    ADD COLUMN media_selection jsonb,
    ADD COLUMN delivery_parts jsonb NOT NULL DEFAULT '{}',
    ADD COLUMN media_conversation_key text,
    ADD COLUMN media_epoch text;
CREATE INDEX inbox_media_history ON chatbot.whatsapp_inbox(media_conversation_key,media_epoch)
    WHERE media_selection IS NOT NULL;
DO $policies$
DECLARE name text;
BEGIN
    FOREACH name IN ARRAY ARRAY['catalog_state','catalog_assets','catalog_uploads','catalog_conversations'] LOOP
        EXECUTE format('ALTER TABLE chatbot.%I ENABLE ROW LEVEL SECURITY',name);
        EXECUTE format('ALTER TABLE chatbot.%I FORCE ROW LEVEL SECURITY',name);
        EXECUTE format('REVOKE ALL ON chatbot.%I FROM PUBLIC,anon,authenticated',name);
        EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON chatbot.%I TO chatbot_app',name);
        EXECUTE format('CREATE POLICY backend_access ON chatbot.%I TO chatbot_app USING (true) WITH CHECK (true)',name);
    END LOOP;
END $policies$;
