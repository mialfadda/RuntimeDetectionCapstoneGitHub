from flask_socketio import SocketIO

socketio = SocketIO()


def send_threat_alert(user_id, url, label, confidence):
    pass


def send_scan_complete(user_id, submission_id, status):
    pass


def send_system_alert(message, alert_type='info'):
    pass
