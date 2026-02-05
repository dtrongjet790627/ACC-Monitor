# -*- coding: utf-8 -*-
"""
ACC Monitor - WebSocket Handlers
"""
from datetime import datetime
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.services.monitor_service import MonitorService
from app.services.database_service import DatabaseService
from app.services.log_service import LogService

# Initialize services
monitor_service = MonitorService()
database_service = DatabaseService()
log_service = LogService()


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected at {datetime.utcnow()}")
    emit('connected', {
        'status': 'connected',
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected at {datetime.utcnow()}")


@socketio.on('join')
def handle_join(data):
    """Join a room for specific updates"""
    room = data.get('room', 'status')
    join_room(room)
    emit('joined', {
        'room': room,
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('leave')
def handle_leave(data):
    """Leave a room"""
    room = data.get('room', 'status')
    leave_room(room)


@socketio.on('request_status')
def handle_status_request(data=None):
    """Handle request for server status"""
    server_id = data.get('server_id') if data else None

    if server_id:
        # Get specific server status
        status = monitor_service.get_all_servers_status()
        server_status = next(
            (s for s in status if s['id'] == server_id), None
        )
        emit('server_status', {
            'server': server_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    else:
        # Get all servers status
        status = monitor_service.get_all_servers_status()
        emit('all_servers_status', {
            'servers': status,
            'timestamp': datetime.utcnow().isoformat()
        })


@socketio.on('request_database_status')
def handle_database_status_request(data=None):
    """Handle request for database status"""
    server_id = data.get('server_id') if data else None

    if server_id:
        db_status = database_service.get_database_status(server_id)
        emit('database_status', {
            'database': db_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    else:
        databases = database_service.get_all_databases_status()
        emit('all_databases_status', {
            'databases': databases,
            'timestamp': datetime.utcnow().isoformat()
        })


@socketio.on('request_alerts')
def handle_alerts_request(data=None):
    """Handle request for alerts"""
    from app.models import Alert

    limit = data.get('limit', 20) if data else 20

    alerts = Alert.query.order_by(
        Alert.created_at.desc()
    ).limit(limit).all()

    emit('alerts', {
        'alerts': [a.to_dict() for a in alerts],
        'timestamp': datetime.utcnow().isoformat()
    })


# ============ Broadcast Functions ============
# These can be called from background tasks to push updates

def broadcast_server_status(server_status):
    """Broadcast server status update to all clients"""
    socketio.emit('server_status_update', {
        'server': server_status,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_alert(alert):
    """Broadcast new alert to all clients"""
    socketio.emit('new_alert', {
        'alert': alert,
        'timestamp': datetime.utcnow().isoformat()
    }, room='alerts')


def broadcast_process_stopped(server_id, process_name):
    """Broadcast process stopped event"""
    socketio.emit('process_stopped', {
        'server_id': server_id,
        'process_name': process_name,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_process_restarted(server_id, process_name, success):
    """Broadcast process restart event"""
    socketio.emit('process_restarted', {
        'server_id': server_id,
        'process_name': process_name,
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_tablespace_warning(server_id, tablespace_name, usage_percent):
    """Broadcast tablespace warning"""
    socketio.emit('tablespace_warning', {
        'server_id': server_id,
        'tablespace_name': tablespace_name,
        'usage_percent': usage_percent,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_log_alert(server_id, level, message):
    """Broadcast log alert"""
    socketio.emit('log_alert', {
        'server_id': server_id,
        'level': level,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }, room='alerts')
