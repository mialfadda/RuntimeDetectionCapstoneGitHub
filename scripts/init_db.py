import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.database.models import db


def init_database():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("All tables created successfully.")


if __name__ == '__main__':
    init_database()
