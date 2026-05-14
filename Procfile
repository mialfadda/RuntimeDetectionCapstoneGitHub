web: sh -c 'python scripts/init_db.py && gunicorn -w 2 --bind 0.0.0.0:$PORT --timeout 120 run:app'
