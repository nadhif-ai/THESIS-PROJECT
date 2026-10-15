from app.admin import store


def test_application_role_and_schema_are_private(pg_workspace):
    with pg_workspace.admin_connection() as db:
        assert db.execute("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname='chatbot_app'").fetchone()[0] is False
        for role in ("anon", "authenticated"):
            assert db.execute("SELECT has_schema_privilege(%s,'chatbot','USAGE')", (role,)).fetchone()[0] is False
        assert db.execute("SELECT count(*) FROM pg_tables WHERE schemaname='chatbot' AND NOT rowsecurity").fetchone()[0] == 0
