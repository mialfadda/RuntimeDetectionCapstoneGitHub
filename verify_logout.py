"""Verify JWT logout actually revokes the token."""
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database.models import db


def main():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        c = app.test_client()

        # 1. Register
        r = c.post('/auth/register', json={'email': 'jwt@test.com',
                                          'password': 'password123'})
        assert r.status_code == 201, r.get_json()
        access = r.get_json()['access_token']
        H = {'Authorization': f'Bearer {access}'}

        # 2. Use token — should be 200
        r = c.get('/detections', headers=H)
        assert r.status_code == 200, f"pre-logout failed: {r.status_code} {r.get_json()}"
        print(f"PASS  pre-logout  GET /detections -> {r.status_code}")

        # 3. Logout
        r = c.post('/auth/logout', headers=H)
        assert r.status_code == 200, r.get_json()
        print(f"PASS  logout       POST /auth/logout -> {r.status_code}")

        # 4. Reuse same token — should be 401
        r = c.get('/detections', headers=H)
        assert r.status_code == 401, f"post-logout should 401, got {r.status_code} {r.get_json()}"
        print(f"PASS  post-logout GET /detections -> {r.status_code} (token revoked)")

        print()
        print("Logout revocation verified.")


if __name__ == '__main__':
    main()
