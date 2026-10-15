ALTER TABLE chatbot.runtime_control
 ADD COLUMN maintenance_started_at text,
 ADD COLUMN intake_started_at text;
UPDATE chatbot.runtime_control
 SET maintenance_started_at=cutover_started_at,
     intake_started_at=CASE WHEN mode IN ('intake','live') THEN cutover_started_at END;
INSERT INTO chatbot.schema_migrations VALUES(2);
