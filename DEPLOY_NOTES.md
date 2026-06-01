# Deployment Notes — async_mode vs gunicorn worker (RECONCILE BEFORE ANY DEPLOY)

> Added during the `integration` ← `upstream/master` merge (2026-06-01). The demo
> runs **local-only** (`python run.py`), so this mismatch is documented, not yet fixed.

## The mismatch
- **App code** (`app/api/websocket.py`, commit 5e44a52): Flask-SocketIO is created with
  `async_mode='threading'`. This is what `python run.py` uses locally and must keep working —
  it avoids engineio's eventlet auto-detect, which breaks on Python 3.12+.
- **Deploy config** (`railway.json`): start command is a **sync** gunicorn worker
  (`gunicorn -w 2 ... run:app`). The historical `mialfadda` intent was eventlet → **gevent**
  worker, but at the `upstream/master` tip there is **no gevent/eventlet** — neither in
  `requirements.txt` nor as a `-k` worker class. `Procfile` was removed; `railway.json` is the
  only deploy descriptor.

## Why it's incompatible
Flask-SocketIO websockets need a single async worker whose class **matches** the configured
`async_mode`. The current combo is broken for real-time use two ways:
- `async_mode='threading'` + `gunicorn -w 2` (sync, multi-worker): websocket/Socket.IO
  sessions are not sticky across the 2 workers and long-poll/upgrade handling is unreliable.
- If a `gevent`/`eventlet` worker is ever reintroduced (the old mialfadda plan) **without**
  flipping `async_mode` to match, engineio will misbehave.

## Before any future deploy — pick ONE and align both ends
1. **Keep threading**: run a single threaded worker — `gunicorn -w 1 --threads N -k gthread
   run:app` (or `python run.py` behind a reverse proxy). Leave `async_mode='threading'`.
2. **Go async**: add `gevent` + `gevent-websocket` to `requirements.txt`, use
   `-k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1`, and set
   `async_mode='gevent'`.

Do **not** ship `async_mode='threading'` with a multi-worker sync/async gunicorn command.
