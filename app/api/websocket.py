from flask_socketio import SocketIO, emit, join_room, leave_room
from app.utils.logger import get_api_logger

logger = get_api_logger()

# ─── SOCKETIO INSTANCE ──────────────────────────────────────
# async_mode='threading' works with our Flask dev server
socketio = SocketIO(cors_allowed_origins='*', async_mode='threading')


# ─── CONNECTION EVENTS ──────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    """Called when a client connects"""
    logger.info('websocket_connected', extra={'event': 'connect'})
    emit('connected', {'message': 'Connected to threat detection system'})


@socketio.on('disconnect')
def handle_disconnect():
    """Called when a client disconnects"""
    logger.info('websocket_disconnected', extra={'event': 'disconnect'})


# ─── ROOM EVENTS ────────────────────────────────────────────
# Rooms let us send alerts to specific users only

@socketio.on('join')
def handle_join(data):
    """
    Client joins a room to receive their personal alerts.
    Usage from browser: socket.emit('join', {room: 'user_1'})
    """
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room, 'message': f'Joined room {room}'})
        logger.info('websocket_join', extra={'room': room})


@socketio.on('leave')
def handle_leave(data):
    """Client leaves a room"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left', {'room': room})


# ─── THREAT ALERT HELPERS ───────────────────────────────────
# These functions are called by other parts of the system
# to push alerts to connected clients

def send_threat_alert(user_id, url, label, confidence):
    """
    Sends a real-time threat alert to a specific user.
    Called after ML model makes a prediction.

    Usage: send_threat_alert(user_id=1, url='http://evil.com',
                             label='phishing', confidence=95.0)
    """
    room = f'user_{user_id}'
    socketio.emit('threat_alert', {
        'url': url,
        'label': label,
        'confidence': confidence,
        'threat_level': 'HIGH' if label == 'phishing' else 'LOW',
        'message': f'Threat detected: {url} classified as {label} '
                  f'with {confidence}% confidence'
    }, room=room)

    logger.info('threat_alert_sent', extra={
        'user_id': user_id,
        'url': url,
        'label': label,
        'confidence': confidence
    })


def send_scan_complete(user_id, submission_id, status):
    """
    Notifies user when their URL scan is complete.

    Usage: send_scan_complete(user_id=1, submission_id=5, status='complete')
    """
    room = f'user_{user_id}'
    socketio.emit('scan_complete', {
        'submission_id': submission_id,
        'status': status,
        'message': f'Scan {submission_id} completed with status: {status}'
    }, room=room)


def send_system_alert(message, alert_type='info'):
    """
    Broadcasts a system-wide alert to ALL connected clients.
    Used for maintenance notices or critical system events.

    Usage: send_system_alert('System maintenance in 5 minutes', 'warning')
    """
    socketio.emit('system_alert', {
        'message': message,
        'type': alert_type
    }, broadcast=True)

    logger.info('system_alert_sent', extra={
        'message': message,
        'type': alert_type
    })