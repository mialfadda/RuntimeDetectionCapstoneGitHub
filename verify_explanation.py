"""Verify GET /explanations/{scan_id} returns the stored, URL-specific rationale."""
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

        # Register and grab a token
        r = c.post('/auth/register', json={'email': 'exp@test.com',
                                          'password': 'password123'})
        access = r.get_json()['access_token']
        H = {'Authorization': f'Bearer {access}'}

        # Scan a URL
        target = 'http://paypal-secure-login.tk/verify'
        r = c.post('/scan/analyze', headers=H,
                   json={'url': target, 'source': 'verify'})
        assert r.status_code == 200, r.get_json()
        scan = r.get_json()
        sid = scan['scan_id']
        print(f"scan_id={sid}  risk={scan['risk_level']}  confidence={scan['confidence']}")

        # Fetch explanation
        r = c.get(f'/explanations/{sid}', headers=H)
        assert r.status_code == 200, r.get_json()
        exp = r.get_json()
        print()
        print(f"method:          {exp.get('method')}")
        print(f"summary_text:    {exp.get('summary_text')}")
        print(f"top_features:    {len(exp.get('top_features', []))} features")
        for name, score in (exp.get('top_features') or []):
            print(f"  - {name:20s} {score}")
        print(f"shap_values:     {len(exp.get('shap_values') or {})} keys")
        print(f"confidence:      {exp.get('confidence')}")
        print(f"created_at:      {exp.get('created_at')}")

        # Critical assertions per the task spec
        st = exp.get('summary_text') or ''
        assert target in st, (
            "summary_text should mention the actual URL, "
            "got: " + st
        )
        assert scan['risk_level'] in st, (
            "summary_text should mention the risk level, got: " + st
        )
        assert isinstance(exp.get('top_features'), list) and len(exp['top_features']) > 0
        assert isinstance(exp.get('shap_values'), dict) and len(exp['shap_values']) > 0
        assert exp.get('confidence') is not None
        assert exp.get('created_at') is not None

        print()
        print("PASS — stored explanation returned with URL-specific rationale.")


if __name__ == '__main__':
    main()
