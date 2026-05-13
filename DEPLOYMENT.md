# RUNTIME MALWEB DETECTOR — Cloud Deployment

This repository is wired for a three-service deployment:

- **Database**  → Supabase (Postgres)
- **API**       → Railway (Flask + gunicorn + eventlet)
- **Dashboard** → Vercel (Vite/React static)
- **Extension** → Chrome unpacked, points at the Railway URL

The code is already production-ready. What's left is three browser
sign-ups and pasting URLs between them. **All three services have a
free tier sufficient for the project demo.**

---

## STEP 1 — Create Supabase Database

```
┌─────────────────────────────────────────────────────┐
│ MANUAL STEP: Set up Supabase Database               │
│                                                     │
│ 1. Go to https://supabase.com                       │
│ 2. Sign up / log in with GitHub                     │
│ 3. Click "New Project"                              │
│ 4. Name it: runtime-malweb-detector                 │
│ 5. Choose a strong database password — save it!     │
│ 6. Select region: Middle East (or closest to you)   │
│ 7. Wait for project to finish creating (~2 min)     │
│ 8. Go to: Settings → Database → Connection string   │
│ 9. Select "URI" format and copy the full string:    │
│    postgresql://postgres:[PASSWORD]@[HOST]:5432/    │
│    postgres                                         │
│ 10. Save this — you will paste it into Railway next │
└─────────────────────────────────────────────────────┘
```

Keep the connection string handy — it becomes Railway's
`DATABASE_URL`.

---

## STEP 2 — Deploy Flask backend to Railway

```
┌─────────────────────────────────────────────────────┐
│ MANUAL STEP: Deploy Flask backend to Railway        │
│                                                     │
│ 1. Go to https://railway.app                        │
│ 2. Sign up / log in with GitHub                     │
│ 3. Click "New Project"                              │
│ 4. Select "Deploy from GitHub repo"                 │
│ 5. Choose: RuntimeDetectionCapstoneGitHub           │
│ 6. Railway auto-detects Python — confirm Procfile   │
│ 7. Go to Variables tab, add these env vars:         │
│                                                     │
│    DATABASE_URL   = (paste Supabase URI)            │
│    JWT_SECRET_KEY = (random 32-char string)         │
│    SECRET_KEY     = (different random 32-char)      │
│    FLASK_ENV      = production                      │
│    FRONTEND_URL   = (add Vercel URL after Step 3)   │
│                                                     │
│ 8. Click Deploy                                     │
│ 9. Wait for build (~3-5 min)                        │
│ 10. Copy your Railway public URL:                   │
│     e.g. https://runtimemalweb.railway.app          │
│ 11. Share this URL — this is your API endpoint      │
└─────────────────────────────────────────────────────┘
```

**Generating random secrets (one-liner)** — run locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run it twice — one value for `JWT_SECRET_KEY`, one for `SECRET_KEY`.

**Procfile** at the repo root tells Railway how to start the app:

```
web: python scripts/apply_migrations.py && gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT run:app
```

The migration script runs `flask db upgrade` against the configured
`DATABASE_URL` before gunicorn starts, so Supabase gets the same
schema as the local SQLite DB.

---

## STEP 3 — Deploy React dashboard to Vercel

```
┌─────────────────────────────────────────────────────┐
│ MANUAL STEP: Deploy React dashboard to Vercel       │
│                                                     │
│ 1. Go to https://vercel.com                         │
│ 2. Sign up / log in with GitHub                     │
│ 3. Click "Add New Project"                          │
│ 4. Import: RuntimeDetectionCapstoneGitHub           │
│ 5. Set Root Directory to: dashboard                 │
│ 6. Framework Preset: Vite                           │
│ 7. Under Environment Variables add:                 │
│    VITE_API_URL = https://YOUR-RAILWAY-URL.railway  │
│ 8. Click Deploy                                     │
│ 9. Wait for build (~2-3 min)                        │
│ 10. Copy your Vercel URL:                           │
│     e.g. https://runtimemalweb.vercel.app           │
│ 11. Go BACK to Railway → Variables                  │
│     Update FRONTEND_URL = your Vercel URL           │
│ 12. Redeploy Railway so CORS picks up the new URL   │
└─────────────────────────────────────────────────────┘
```

`vercel.json` (already in `dashboard/`) handles the SPA fallback so
client-side routes (`/scan`, `/app`, `/explanation/123`) all serve
`index.html`.

---

## STEP 4 — Update the extension with the real Railway URL

After Railway gives you a URL, **come back here** and tell me the URL.
I'll then replace `REPLACE-WITH-RAILWAY-URL.railway.app` in:

- `extension/background.js` (DEFAULT_API_BASE)
- `extension/manifest.json` (host_permissions)
- `dashboard/.env.production` (VITE_API_URL — Vercel rebuilds when this changes)

…and push a follow-up commit.

If you'd rather do it yourself, search the repo for
`REPLACE-WITH-RAILWAY-URL.railway.app` and replace every match
with your actual Railway hostname (no trailing slash).

---

## STEP 5 — Load the extension in Chrome

```
1. Open chrome://extensions
2. Enable Developer Mode (top right toggle)
3. Click "Load unpacked"
4. Select the extension/ folder in the repo
5. The RUNTIME MALWEB DETECTOR icon appears in toolbar
6. Click it, enter your Railway URL in Settings → API Base URL
7. Log in with your demo account
```

---

## STEP 6 — Verify the deployment

```powershell
# health
curl https://YOUR-RAILWAY-URL/health
# { "status": "healthy", "service": "RUNTIME MALWEB DETECTOR" }

# register
curl -X POST https://YOUR-RAILWAY-URL/auth/register `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"Demo\",\"email\":\"demo@demo.com\",\"password\":\"demo1234\"}"

# login → copy access_token from response
curl -X POST https://YOUR-RAILWAY-URL/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"demo@demo.com\",\"password\":\"demo1234\"}"

# scan
curl -X POST https://YOUR-RAILWAY-URL/scan/analyze `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"url\":\"https://www.youtube.com\",\"source\":\"dashboard\"}"
```

In the browser:

1. Open `https://YOUR-VERCEL-URL`
2. Confirm "RUNTIME MALWEB DETECTOR" banner
3. Log in, scan a URL, see the verdict + confidence
4. Open an explanation page — should show URL-specific rationale
5. Log out, then refresh — protected pages should bounce to login

---

## Architecture (matches the design document)

```
        Client Browser
              │
   ┌──────────┼──────────┐
   │          │          │
 Dashboard  Extension  curl/api
 (Vercel)   (Chrome)
              │
              ▼
         Railway (API Gateway)
            Flask + Gunicorn
              │
              ├──► Supabase Postgres   (DATABASE_URL)
              └──► In-process ML       (scikit-learn RandomForest)
```

The "AI Detection Server" from the design lives in-process on Railway
for cost/simplicity; if you ever want to split it out, point
`app/interfaces/mocks.py` at an HTTP service instead of importing
`malicious_detector.predict`.
