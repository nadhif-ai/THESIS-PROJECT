"""Persist derived chunk counts without changing knowledge records or namespaces."""

from app.admin import store


def main():
    try:
        store.check_ready()
        print(f"Updated chunk metadata for {store.backfill_version_counts()} versions.")
    finally:
        store.close_pool()


if __name__ == "__main__":
    main()
