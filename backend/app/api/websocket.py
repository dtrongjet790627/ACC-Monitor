# -*- coding: utf-8 -*-
"""
ACC Monitor - WebSocket Handlers
"""
from datetime import datetime
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.services.monitor_service import MonitorService
from app.services.database_service import DatabaseService
from app.services.log_service import LogService, initialize_system_logs

# Initialize services
monitor_service = MonitorService()
database_service = DatabaseService()
log_service = LogService()

# Initialize system logs on module load
initialize_system_logs()


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected at {datetime.utcnow()}")

    # Add connection log with descriptive message
    log_entry = log_service.add_system_log('info', 'SYSTEM', 'Dashboard client connected')
    broadcast_system_log(log_entry)

    emit('connected', {
        'status': 'connected',
        'timestamp': datetime.utcnow().isoformat()
    })

    # Send recent system logs to newly connected client (50 entries for richer history)
    recent_logs = log_service.get_system_logs(50)
    emit('system_logs_batch', {
        'logs': recent_logs,
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


def broadcast_server_recovered(server_id, offline_duration):
    """Broadcast server recovery event"""
    socketio.emit('server_recovered', {
        'server_id': server_id,
        'offline_duration': offline_duration,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_server_offline(server_id):
    """Broadcast server offline event"""
    socketio.emit('server_offline', {
        'server_id': server_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_connection_state_change(server_id, new_state, old_state):
    """Broadcast connection state change (online/offline/warning)"""
    socketio.emit('connection_state_change', {
        'server_id': server_id,
        'new_state': new_state,
        'old_state': old_state,
        'timestamp': datetime.utcnow().isoformat()
    }, room='status')


def broadcast_system_log(log_entry):
    """
    Broadcast a system log entry to all clients
    log_entry format: {time, timestamp, level, server_id, message}
    """
    socketio.emit('system_log', {
        'log': log_entry,
        'timestamp': datetime.utcnow().isoformat()
    })


def broadcast_system_logs_batch(logs):
    """
    Broadcast multiple system logs at once (for initial connection)
    """
    socketio.emit('system_logs_batch', {
        'logs': logs,
        'timestamp': datetime.utcnow().isoformat()
    })


def ingest_agent_alert(server_id, message, level='info'):
    """
    Write an agent-reported log entry into the system log buffer and broadcast it.
    Called from the /agent/report route so agent logs appear in the EAI System Log panel.
    Level is extracted from the log message content by the caller (info/warning/error/critical).
    """
    from config.settings import SERVERS
    server_config = SERVERS.get(server_id, {})
    server_name = server_config.get('name_cn', server_config.get('name', server_id))
    short_msg = message[:100] + '...' if len(message) > 100 else message
    log_entry = log_service.add_system_log(level, server_id, f"{server_name}: {short_msg}")
    broadcast_system_log(log_entry)


@socketio.on('request_system_logs')
def handle_system_logs_request(data=None):
    """Handle request for system logs"""
    count = data.get('count', 50) if data else 50
    logs = log_service.get_system_logs(count)
    emit('system_logs_batch', {
        'logs': logs,
        'timestamp': datetime.utcnow().isoformat()
    })
