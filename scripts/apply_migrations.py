"""Run Alembic migrations against the configured DATABASE_URL."""
import os
import sys

# Fix Python path so 'app' module is found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        print(f"[migrate] upgrade failed: {e}", flush=True)
        from app import create_app
        from app.database.models import db
        a = create_app()
        with a.app_context():
            db.create_all()
            print("[migrate] db.create_all() applied as fallback", flush=True)
        sys.exit(0)
