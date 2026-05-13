"""End-to-end smoke test of all backend endpoints using Flask's test client."""
import json
import os
import sys

# create_app() reads DATABASE_URL — set it before importing so we get a
# truly isolated in-memory DB.
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database.models import db


def main():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        c = app.test_client()
        results = []

        def check(label, resp, expect=200):
            ok = resp.status_code == expect
            try:
                body = resp.get_json()
            except Exception:
                body = resp.data[:200]
            results.append((ok, label, resp.status_code, body))
            print(f"{'OK ' if ok else 'FAIL'}  [{resp.status_code}] {label}")
            return body

        # 1. /health
        check("GET /health", c.get('/health'))

        # 2. register
        reg = check("POST /auth/register",
                    c.post('/auth/register', json={'email': 'smoke@test.com',
                                                   'password': 'password123'}),
                    expect=201)
        access = reg['access_token']; refresh = reg['refresh_token']
        H = {'Authorization': f'Bearer {access}'}
        Href = {'Authorization': f'Bearer {refresh}'}

        # 3. login
        login = check("POST /auth/login",
                      c.post('/auth/login', json={'email': 'smoke@test.com',
                                                   'password': 'password123'}))

        # 4. refresh
        check("POST /auth/refresh", c.post('/auth/refresh', headers=Href))

        # 5. /auth/me
        check("GET /auth/me", c.get('/auth/me', headers=H))

        # 6-8. scan three known URLs
        scan_yt = check("POST /scan/analyze YouTube",
                        c.post('/scan/analyze',
                               headers=H,
                               json={'url': 'https://www.youtube.com'}))
        scan_phish = check("POST /scan/analyze phishing",
                           c.post('/scan/analyze',
                                  headers=H,
                                  json={'url': 'http://paypal-secure-login.tk/verify'}))
        scan_google = check("POST /scan/analyze Google",
                            c.post('/scan/analyze',
                                   headers=H,
                                   json={'url': 'https://www.google.com'}))

        print()
        print("=== Confidence sanity ===")
        for s in (scan_yt, scan_phish, scan_google):
            print(f"  {s['url']:50s} {s['risk_level']:10s} {s['confidence']}")
        print()

        # 9. batch
        check("POST /scan/batch",
              c.post('/scan/batch', headers=H,
                     json={'urls': ['https://example.com', 'https://github.com']}))

        # 10. detections
        det = check("GET /detections", c.get('/detections', headers=H))
        for d in det['detections']:
            assert 'risk_level' in d and 'confidence' in d, \
                f"detections row missing fields: {d}"
        print(f"  -> {len(det['detections'])} detections, all have risk_level/confidence")

        # 11. detections by id
        sid = scan_yt['scan_id']
        check(f"GET /detections/{sid}",
              c.get(f'/detections/{sid}', headers=H))

        # 12. explanation
        exp = check(f"GET /explanations/{sid}",
                    c.get(f'/explanations/{sid}', headers=H))
        print(f"  -> method={exp.get('method')} top_features={len(exp.get('top_features',[]))}")

        # 13. generate explanation
        check("POST /explanations/generate",
              c.post('/explanations/generate', headers=H,
                     json={'scan_id': sid}),
              expect=201)

        # 14. dashboard metrics
        m = check("GET /dashboard/metrics", c.get('/dashboard/metrics', headers=H))
        print(f"  -> total={m['total_scans']} completed={m['completed_scans']} pending={m['pending_scans']}")

        # 15. reports
        check("GET /dashboard/reports", c.get('/dashboard/reports', headers=H))

        # 16. logout
        check("POST /auth/logout", c.post('/auth/logout', headers=H))

        fails = [r for r in results if not r[0]]
        print()
        print(f"=== {len(results)-len(fails)}/{len(results)} endpoints OK ===")
        if fails:
            for ok, label, code, body in fails:
                print(f"FAIL {label} -> {code} {body}")
            sys.exit(1)


if __name__ == '__main__':
    main()
