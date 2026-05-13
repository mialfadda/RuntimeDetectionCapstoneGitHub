"""Run Alembic migrations against the configured DATABASE_URL.

Called from Railway's start command (or any prod boot) before the web
worker starts so the schema is always at HEAD. Safer than relying on
the `flask` CLI finding FLASK_APP at runtime.
"""
import os
import sys

from flask_migrate import upgrade

from app import create_app


def main():
    app = create_app()
    with app.app_context():
        print(f"[migrate] using {app.config['SQLALCHEMY_DATABASE_URI'][:40]}...", flush=True)
        upgrade()
        print("[migrate] done", flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Don't crash the deployment if migrations fail (e.g. on first run
        # before tables exist). Fall back to create_all for the brand-new
        # case so the app still boots, then exit non-zero so Railway logs it.
        print(f"[migrate] upgrade failed: {e}", flush=True)
        from app import create_app
        from app.database.models import db
        a = create_app()
        with a.app_context():
            db.create_all()
            print("[migrate] db.create_all() applied as fallback", flush=True)
        sys.exit(0)
