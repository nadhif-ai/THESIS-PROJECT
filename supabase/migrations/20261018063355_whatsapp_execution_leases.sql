ALTER TABLE chatbot.whatsapp_inbox
  ADD COLUMN lease_token text,
  ADD COLUMN lease_expires_at timestamptz,
  ADD COLUMN generation_started_at timestamptz,
  ADD COLUMN generated_at timestamptz,
  ADD COLUMN send_started_at timestamptz,
  ADD COLUMN sent_at timestamptz;

CREATE INDEX inbox_chat_pending ON chatbot.whatsapp_inbox(session,sender,created_at,message_id)
  WHERE status IN ('queued','generating','sending');
