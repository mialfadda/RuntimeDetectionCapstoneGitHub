from flask_socketio import SocketIO

# `async_mode='threading'` avoids engineio's eventlet auto-detect, which
# fails on Python 3.12+ because eventlet still references
# `ssl.wrap_socket` (removed in 3.12). The production server already
# moved off eventlet (sync gunicorn) so this also matches deploy reality.
socketio = SocketIO(async_mode='threading')


def send_threat_alert(user_id, url, label, confidence):
    pass


def send_scan_complete(user_id, submission_id, status):
    pass


def send_system_alert(message, alert_type='info'):
    pass
