import json
import sqlite3
import pytest
from app.admin import store
from scripts.migrate_state import snapshot, import_snapshot, verify_snapshot, rollback_check, set_runtime_mode


@pytest.fixture
def source_snapshot(tmp_path):
    from scripts.migrate_state import COLUMNS, KEYS, REAL, INTEGER
    path=tmp_path/'source.sqlite3'
    with sqlite3.connect(path) as db:
        for table, columns in COLUMNS.items():
            definitions=[f'"{c}" '+('REAL' if (table,c) in REAL else 'INTEGER' if (table,c) in INTEGER else 'TEXT') for c in columns]
            definitions.append('PRIMARY KEY('+','.join(KEYS[table])+')')
            db.execute(f'CREATE TABLE {table} ({",".join(definitions)})')
        db.execute("INSERT INTO settings VALUES ('published_version','\"version-1\"')")
        db.execute("INSERT INTO users VALUES ('admin','00000000000000000000000000000000','copied-hash')")
        db.execute("INSERT INTO sessions VALUES ('expired',1.0,'csrf')")
        db.execute("INSERT INTO versions VALUES ('version-1','retained','published','time','{}','[]',NULL)")
        db.execute("INSERT INTO jobs VALUES ('job-1','evaluate','completed','{}','{}',NULL,'time','time','{}')")
        db.execute("INSERT INTO conversations VALUES (41,'s','playground','question','answer','{}',1.5,NULL,'time')")
        db.execute("INSERT INTO whatsapp_inbox VALUES ('asia-chatbot','old','123@lid','old body','sent','answer',NULL,'[\"reply-old\"]',NULL,'time','time')")
        db.execute("INSERT INTO whatsapp_receipts VALUES ('reply-old',2,'time')")
    return path


def test_backup_includes_committed_wal_rows(tmp_path):
    source=tmp_path/'wal.sqlite3'
    with sqlite3.connect(source) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE sample(id INTEGER PRIMARY KEY,value TEXT)')
        db.execute("INSERT INTO sample VALUES (41,'retained')")
        db.commit()
        snapshot(source,tmp_path/'private'/'backup.sqlite3')
    with sqlite3.connect(tmp_path/'private'/'backup.sqlite3') as db:
        assert db.execute('SELECT * FROM sample').fetchone()==(41,'retained')
    assert (tmp_path/'private'/'backup.sqlite3').stat().st_mode & 0o777 == 0o600


def test_import_repeat_verify_sequence_and_preserved_fields(source_snapshot,pg_workspace):
    result=import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    assert result['status']=='imported'
    assert verify_snapshot(source_snapshot,pg_workspace.admin_dsn)['verified']
    assert import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')['status']=='already-imported'
    with pg_workspace.admin_connection() as db:
        assert db.execute("SELECT salt,password_hash FROM chatbot.users").fetchone()[1]=='copied-hash'
        assert db.execute('SELECT trace_id FROM chatbot.conversations').fetchone()[0] is None
        assert db.execute('SELECT expires FROM chatbot.sessions').fetchone()[0]==1.0
        assert db.execute("INSERT INTO chatbot.conversations(question) VALUES ('new') RETURNING id").fetchone()[0]==42
    with pytest.raises(ValueError,match='content'):
        verify_snapshot(source_snapshot,pg_workspace.admin_dsn)


def test_equal_counts_do_not_hide_changed_content(source_snapshot,pg_workspace):
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    with pg_workspace.admin_connection() as db:
        db.execute("UPDATE chatbot.conversations SET answer='different' WHERE id=41")
    with pytest.raises(ValueError,match='content'):
        verify_snapshot(source_snapshot,pg_workspace.admin_dsn)
    assert import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')['status']=='already-imported'
    with pg_workspace.admin_connection() as db:
        assert db.execute('SELECT answer FROM chatbot.conversations').fetchone()[0]=='different'


@pytest.mark.parametrize('change',[
 'CREATE TABLE unexpected(id TEXT)',
 'ALTER TABLE users ADD COLUMN unexpected TEXT',
 "UPDATE versions SET status='ready'",
 "UPDATE jobs SET payload='invalid'",
 'DELETE FROM settings',
 'DELETE FROM conversations; DELETE FROM versions; DELETE FROM users; DELETE FROM settings; DELETE FROM sessions; DELETE FROM jobs; DELETE FROM whatsapp_inbox; DELETE FROM whatsapp_receipts',
])
def test_bad_source_aborts_before_any_import(source_snapshot,pg_workspace,change):
    with sqlite3.connect(source_snapshot) as db:
        db.executescript(change)
    with pytest.raises(ValueError):
        import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    with pg_workspace.admin_connection() as db:
        assert db.execute('SELECT count(*) FROM chatbot.users').fetchone()[0]==0


def test_wrong_project_and_nonempty_destination_refused(source_snapshot,pg_workspace):
    with pytest.raises(ValueError,match='identity'):
        import_snapshot(source_snapshot,pg_workspace.admin_dsn,'wrong-project')
    with pg_workspace.admin_connection() as db:
        db.execute("INSERT INTO chatbot.settings VALUES ('existing','true')")
    with pytest.raises(ValueError,match='empty'):
        import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')


def test_import_failure_rolls_back_every_table(source_snapshot,pg_workspace):
    with pg_workspace.admin_connection() as db:
        db.execute("ALTER TABLE chatbot.whatsapp_receipts ADD CONSTRAINT reject_synthetic CHECK(ack=4)")
    with pytest.raises(Exception):
        import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    with pg_workspace.admin_connection() as db:
        assert db.execute('SELECT count(*) FROM chatbot.users').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM chatbot.state_imports').fetchone()[0]==0


def test_legacy_progress_and_first_intake_blocks_rollback(source_snapshot,pg_workspace):
    with sqlite3.connect(source_snapshot) as db:
        db.execute('ALTER TABLE jobs DROP COLUMN progress')
    import_snapshot(source_snapshot,pg_workspace.admin_dsn,'local-rehearsal')
    assert rollback_check(pg_workspace.admin_dsn)['allowed']
    with pytest.raises(ValueError,match='reconciliation'):
        set_runtime_mode('live',pg_workspace.admin_dsn)
    set_runtime_mode('intake',pg_workspace.admin_dsn)
    assert store.enqueue_inbox('asia-chatbot','new-after-cutover','123@lid','new')
    assert not rollback_check(pg_workspace.admin_dsn)['allowed']
    with pg_workspace.admin_connection() as db:
        assert db.execute('SELECT progress FROM chatbot.jobs').fetchone()[0]=='{}'
