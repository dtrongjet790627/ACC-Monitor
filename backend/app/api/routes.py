# -*- coding: utf-8 -*-
"""
ACC Monitor - REST API Routes
"""
from datetime import datetime
from flask import request, jsonify
from app.api import api_bp
from app.services.monitor_service import MonitorService
from app.services.database_service import DatabaseService
from app.services.restart_service import RestartService
from app.services.log_service import LogService
from app.models import Server, Alert, RestartLog, StationAlert
from app import db
from config.settings import SERVERS, ORACLE_CONFIGS

# Initialize services
monitor_service = MonitorService()
database_service = DatabaseService()
restart_service = RestartService()
log_service = LogService()

# Import agent data service
from app.services.agent_data_service import agent_data_service


# ============ Dashboard API ============

@api_bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get dashboard overview data"""
    # Get all server status
    servers = monitor_service.get_all_servers_status()

    # Count by status
    total = len(servers)
    online = sum(1 for s in servers if s['status'] == 'normal')
    warning = sum(1 for s in servers if s['status'] == 'warning')
    critical = sum(1 for s in servers if s['status'] == 'error')

    # Get recent alerts
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(20).all()

    return jsonify({
        'code': 200,
        'data': {
            'stats': {
                'total_servers': total,
                'online': online,
                'warning': warning,
                'critical': critical
            },
            'servers': servers,
            'recent_alerts': [a.to_dict() for a in recent_alerts],
            'last_update': datetime.utcnow().isoformat()
        }
    })


# ============ Server API ============

@api_bp.route('/servers', methods=['GET'])
def get_servers():
    """Get all servers list"""
    servers = monitor_service.get_all_servers_status()
    return jsonify({
        'code': 200,
        'data': servers
    })


@api_bp.route('/servers/<server_id>', methods=['GET'])
def get_server(server_id):
    """Get single server details"""
    if server_id not in SERVERS:
        return jsonify({
            'code': 404,
            'message': f'Server {server_id} not found'
        }), 404

    server_config = SERVERS[server_id]
    os_type = server_config.get('os', 'windows')

    # Get processes
    if os_type == 'windows':
        processes = monitor_service.check_windows_processes(server_id)
    else:
        processes = monitor_service.check_linux_processes(server_id)

    # Get resources
    resources = monitor_service.check_server_resources(server_id)

    # Get database status if applicable
    db_status = None
    if server_config.get('has_oracle', False):
        db_status = database_service.get_database_status(server_id)

    return jsonify({
        'code': 200,
        'data': {
            'id': server_id,
            'name': server_config['name'],
            'name_cn': server_config.get('name_cn', ''),
            'ip': server_config['ip'],
            'os_type': os_type,
            'status': monitor_service.get_server_status(server_id),
            'processes': processes,
            'cpu_usage': resources.get('cpu_usage', 0),
            'memory_usage': resources.get('memory_usage', 0),
            'disk_usage': resources.get('disk_usage', 0),
            'database': db_status,
            'last_update': datetime.utcnow().isoformat()
        }
    })


@api_bp.route('/servers/<server_id>/status', methods=['GET'])
def get_server_status(server_id):
    """Get server status with processes"""
    if server_id not in SERVERS:
        return jsonify({
            'code': 404,
            'message': f'Server {server_id} not found'
        }), 404

    server_config = SERVERS[server_id]
    os_type = server_config.get('os', 'windows')

    # Get processes
    if os_type == 'windows':
        processes = monitor_service.check_windows_processes(server_id)
        # Also check Windows services (with deduplication)
        services = monitor_service.check_windows_services(server_id)
        if services:
            processes = monitor_service._merge_processes_and_services(processes, services)
    else:
        processes = monitor_service.check_linux_processes(server_id)

    return jsonify({
        'code': 200,
        'data': {
            'server_id': server_id,
            'server_name': server_config['name'],
            'ip': server_config['ip'],
            'status': monitor_service.get_server_status(server_id, processes),
            'processes': processes,
            'last_update': datetime.utcnow().isoformat()
        }
    })


@api_bp.route('/servers/<server_id>/processes', methods=['GET'])
def get_server_processes(server_id):
    """Get processes for a server"""
    if server_id not in SERVERS:
        return jsonify({
            'code': 404,
            'message': f'Server {server_id} not found'
        }), 404

    server_config = SERVERS[server_id]
    os_type = server_config.get('os', 'windows')

    if os_type == 'windows':
        processes = monitor_service.check_windows_processes(server_id)
        # Also check Windows services (with deduplication)
        services = monitor_service.check_windows_services(server_id)
        if services:
            processes = monitor_service._merge_processes_and_services(processes, services)
    else:
        processes = monitor_service.check_linux_processes(server_id)

    return jsonify({
        'code': 200,
        'data': {
            'server_id': server_id,
            'processes': processes
        }
    })


# ============ Process API ============

@api_bp.route('/processes/<server_id>/<process_name>/restart', methods=['POST'])
def restart_process(server_id, process_name):
    """Manually restart a process"""
    if server_id not in SERVERS:
        return jsonify({
            'code': 404,
            'message': f'Server {server_id} not found'
        }), 404

    data = request.get_json() or {}
    reason = data.get('reason', 'Manual restart')

    result = restart_service.restart_process(server_id, process_name, reason)

    # Log to database
    restart_log = RestartLog(
        server_id=server_id,
        process_name=process_name,
        reason=reason,
        success=result['success'],
        error_message=result.get('error_message'),
        log_content=result.get('log_content')
    )
    db.session.add(restart_log)
    db.session.commit()

    return jsonify({
        'code': 200 if result['success'] else 500,
        'data': result
    })


@api_bp.route('/processes/restart-history', methods=['GET'])
def get_restart_history():
    """Get process restart history"""
    server_id = request.args.get('server_id')
    limit = request.args.get('limit', 50, type=int)

    history = restart_service.get_restart_history(server_id, limit)

    return jsonify({
        'code': 200,
        'data': history
    })


# ============ Database API ============

@api_bp.route('/databases', methods=['GET'])
def get_databases():
    """Get all databases status with filtered tablespace data"""
    databases = database_service.get_all_databases_status()

    # Enrich with server config info
    for db_item in databases:
        server_id = db_item.get('server_id')
        if server_id in SERVERS:
            config = SERVERS[server_id]
            db_item['server_name'] = config.get('name', '')
            db_item['server_name_cn'] = config.get('name_cn', '')
            db_item['server_ip'] = config.get('ip', '')

    return jsonify({
        'code': 200,
        'data': databases
    })


@api_bp.route('/databases/<server_id>', methods=['GET'])
def get_database(server_id):
    """Get single database status"""
    if server_id not in ORACLE_CONFIGS:
        return jsonify({
            'code': 404,
            'message': f'Database for server {server_id} not found'
        }), 404

    db_status = database_service.get_database_status(server_id)

    return jsonify({
        'code': 200,
        'data': db_status
    })


@api_bp.route('/databases/<server_id>/tablespaces', methods=['GET'])
def get_tablespaces(server_id):
    """Get tablespace status for a database"""
    if server_id not in ORACLE_CONFIGS:
        return jsonify({
            'code': 404,
            'message': f'Database for server {server_id} not found'
        }), 404

    tablespaces = database_service.get_tablespace_status(server_id)

    return jsonify({
        'code': 200,
        'data': {
            'server_id': server_id,
            'server_ip': SERVERS.get(server_id, {}).get('ip', ''),
            'tablespaces': tablespaces,
            'last_update': datetime.utcnow().isoformat()
        }
    })


@api_bp.route('/databases/<server_id>/optimize', methods=['POST'])
def optimize_database(server_id):
    """One-click database optimization"""
    if server_id not in ORACLE_CONFIGS:
        return jsonify({
            'code': 404,
            'message': f'Database for server {server_id} not found'
        }), 404

    result = database_service.optimize_tablespace(server_id)

    return jsonify({
        'code': 200 if result['success'] else 500,
        'data': result
    })


# ============ Alert API ============

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts list"""
    server_id = request.args.get('server_id')
    level = request.args.get('level')
    acknowledged = request.args.get('acknowledged')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)

    query = Alert.query

    if server_id:
        query = query.filter_by(server_id=server_id)
    if level:
        query = query.filter_by(level=level)
    if acknowledged is not None:
        query = query.filter_by(acknowledged=acknowledged == 'true')

    query = query.order_by(Alert.created_at.desc())

    # Pagination
    total = query.count()
    alerts = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'alerts': [a.to_dict() for a in alerts]
        }
    })


@api_bp.route('/alerts/<int:alert_id>/ack', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    alert = Alert.query.get(alert_id)

    if not alert:
        return jsonify({
            'code': 404,
            'message': 'Alert not found'
        }), 404

    data = request.get_json() or {}
    acknowledged_by = data.get('acknowledged_by', 'system')

    alert.acknowledged = True
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'code': 200,
        'data': alert.to_dict()
    })


@api_bp.route('/alerts/station', methods=['GET'])
def get_station_alerts():
    """Get station alerts from device logs"""
    server_id = request.args.get('server_id')
    station_name = request.args.get('station_name')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)

    query = StationAlert.query

    if server_id:
        query = query.filter_by(server_id=server_id)
    if station_name:
        query = query.filter_by(station_name=station_name)

    query = query.filter_by(resolved=False)
    query = query.order_by(StationAlert.occurred_at.desc())

    total = query.count()
    alerts = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'alerts': [a.to_dict() for a in alerts]
        }
    })


# ============ Log API ============

@api_bp.route('/logs/search', methods=['POST'])
def search_logs():
    """Search logs"""
    data = request.get_json() or {}

    keyword = data.get('keyword', '')
    servers = data.get('servers')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    page = data.get('page', 1)
    page_size = data.get('page_size', 50)

    if not keyword:
        return jsonify({
            'code': 400,
            'message': 'Keyword is required'
        }), 400

    # Parse time filters
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None

    results = log_service.search_logs(
        keyword=keyword,
        server_ids=servers,
        start_time=start_dt,
        end_time=end_dt,
        page=page,
        page_size=page_size
    )

    return jsonify({
        'code': 200,
        'data': results
    })


@api_bp.route('/logs/statistics', methods=['GET'])
def get_log_statistics():
    """Get log statistics"""
    server_id = request.args.get('server_id')
    hours = request.args.get('hours', 24, type=int)

    stats = log_service.get_log_statistics(server_id, hours)

    return jsonify({
        'code': 200,
        'data': stats
    })


# ============ Agent API ============

@api_bp.route('/agent/report', methods=['POST'])
def agent_report():
    """Receive metrics report from agent"""
    data = request.get_json()

    if not data:
        return jsonify({
            'code': 400,
            'message': 'No data provided'
        }), 400

    server_id = data.get('server_id')
    if not server_id:
        return jsonify({
            'code': 400,
            'message': 'server_id is required'
        }), 400

    # Store in agent data service (in-memory for real-time access)
    agent_data_service.update_agent_data(server_id, data)

    # Update or create server record in database
    server = Server.query.get(server_id)
    if not server:
        server_config = SERVERS.get(server_id, {})
        server = Server(
            id=server_id,
            name=server_config.get('name', f'Server {server_id}'),
            name_cn=server_config.get('name_cn', ''),
            ip=server_config.get('ip', ''),
            os_type=server_config.get('os', 'windows')
        )
        db.session.add(server)

    # Update server metrics
    resources = data.get('resources', {})
    server.cpu_usage = resources.get('cpu_usage', 0)
    server.memory_usage = resources.get('memory_usage', 0)
    server.disk_usage = resources.get('disk_usage', 0)
    server.last_check = datetime.utcnow()

    # Determine server status based on processes/containers
    processes = data.get('processes', [])
    containers = data.get('containers', [])
    items = processes + containers

    stopped_count = sum(1 for p in items if p.get('status') == 'stopped')
    if stopped_count > 0:
        server.status = 'error'
    elif resources.get('cpu_usage', 0) > 90 or resources.get('memory_usage', 0) > 90:
        server.status = 'warning'
    else:
        server.status = 'normal'

    # Process alerts from agent (limit to avoid spam)
    # Only date filter: skip log lines whose embedded date is not today.
    # All levels (INFO/WARN/ERROR/FATAL/CRITICAL) are accepted and displayed
    # with their real level extracted from the log message.
    import re
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    # Pattern to extract log level tag from EAI format: [INFO], [WARN], [ERRO], [ERROR], [FATAL], [CRITICAL]
    level_tag_pattern = re.compile(r'\[(INFO|WARN|WARNING|ERRO|ERROR|FATAL|CRITICAL)\]', re.IGNORECASE)

    alerts = data.get('alerts', [])[:50]
    for alert_data in alerts:
        msg = alert_data.get('message', '')

        # Date filter: only today's log lines
        date_match = date_pattern.search(msg)
        if date_match:
            log_date = date_match.group(0)
            if log_date != today_str:
                continue

        # Extract real log level from message content
        level_match = level_tag_pattern.search(msg)
        if level_match:
            raw_level = level_match.group(1).upper()
            if raw_level in ('ERRO', 'ERROR'):
                log_level = 'error'
            elif raw_level in ('WARN', 'WARNING'):
                log_level = 'warning'
            elif raw_level in ('FATAL', 'CRITICAL'):
                log_level = 'critical'
            else:
                log_level = 'info'
        else:
            log_level = 'info'

        # Only persist error/critical level alerts to the Alert table
        if log_level in ('error', 'critical'):
            alert = Alert(
                server_id=server_id,
                level=log_level,
                source='agent',
                message=msg[:500]
            )
            db.session.add(alert)

        # Write ALL levels into the system log buffer for the EAI System Log panel
        from app.api.websocket import ingest_agent_alert
        ingest_agent_alert(server_id, msg, log_level)

    db.session.commit()

    # Broadcast status update via WebSocket
    from app.api.websocket import broadcast_server_status
    broadcast_server_status({
        'id': server_id,
        'name': server.name,
        'name_cn': server.name_cn,
        'ip': server.ip,
        'status': server.status,
        'cpu_usage': server.cpu_usage,
        'memory_usage': server.memory_usage,
        'disk_usage': server.disk_usage,
        'processes': processes,
        'containers': containers,
        'agent_online': True,
        'data_source': 'agent',
        'last_check': server.last_check.isoformat()
    })

    return jsonify({
        'code': 200,
        'message': 'Report received',
        'server_id': server_id,
        'timestamp': datetime.utcnow().isoformat()
    })


@api_bp.route('/agent/status', methods=['GET'])
def get_agents_status():
    """Get status of all monitoring agents"""
    agents = agent_data_service.get_all_agents_status()

    # Add server config info
    for agent in agents:
        server_id = agent['server_id']
        if server_id in SERVERS:
            config = SERVERS[server_id]
            agent['server_name'] = config.get('name', '')
            agent['server_ip'] = config.get('ip', '')

    return jsonify({
        'code': 200,
        'data': {
            'agents': agents,
            'total': len(agents),
            'online': sum(1 for a in agents if a.get('agent_online')),
            'offline': sum(1 for a in agents if not a.get('agent_online')),
            'timestamp': datetime.utcnow().isoformat()
        }
    })


@api_bp.route('/agent/eai-logs', methods=['POST'])
def agent_eai_logs():
    """
    Receive EAI log parsing results from the Linux Agent (Phase 3).
    The Agent on 163 monitors EAI log files locally via tail -F,
    parses report records, and uploads them here for Oracle insertion.
    This replaces the standalone eai_log_monitor SSH-based service on 165.
    """
    import logging
    eai_logger = logging.getLogger('eai_logs')

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': 'No data provided'}), 400

    server_id = data.get('server_id')
    schema = data.get('schema')
    records = data.get('records', [])

    if not schema:
        return jsonify({'code': 400, 'message': 'schema is required'}), 400

    if not records:
        return jsonify({
            'code': 200,
            'message': 'No records to insert',
            'data': {'inserted': 0, 'duplicates': 0}
        })

    # Database configuration for EAI schemas
    # These match the original eai_log_monitor config.py ACC_DATABASE settings
    EAI_DB_CONFIG = {
        'host': '172.17.10.165',
        'port': 1521,
        'service': 'orcl.ecdag.com',
        'schemas': {
            'dpepp1': {'user': 'iplant_dpepp1', 'password': 'acc'},
            'smt2': {'user': 'iplant_smt2', 'password': 'acc'},
            'dpeps1': {'user': 'iplant_dpeps1', 'password': 'acc'}
        }
    }

    schema_config = EAI_DB_CONFIG['schemas'].get(schema)
    if not schema_config:
        return jsonify({'code': 400, 'message': f'Unknown schema: {schema}'}), 400

    inserted = 0
    duplicates = 0
    errors_list = []

    try:
        import cx_Oracle
        dsn = f"{EAI_DB_CONFIG['host']}:{EAI_DB_CONFIG['port']}/{EAI_DB_CONFIG['service']}"
        conn = cx_Oracle.connect(
            user=schema_config['user'],
            password=schema_config['password'],
            dsn=dsn,
            encoding='UTF-8'
        )
        cursor = conn.cursor()

        for record in records:
            try:
                schb_number = record.get('schb_number', '')
                if not schb_number:
                    continue

                is_success = record.get('is_success', True)
                error_message = (record.get('error_message', '') or '')[:2000]
                source_bill_no = record.get('source_bill_no', '') or 'UNKNOWN'

                # MERGE INTO (upsert) - matches original db_handler.py logic exactly
                sql = """
                MERGE INTO ACC_ERP_REPORT_SUCCESS t
                USING (SELECT :schb_number AS SCHB_NUMBER FROM DUAL) s
                ON (t.SCHB_NUMBER = s.SCHB_NUMBER)
                WHEN NOT MATCHED THEN
                INSERT (ID, WONO, PACKID, PARTNO, CNT, LINE, SCHB_NUMBER,
                        SOURCE_BILL_NO, REPORT_TIME, IS_SUCCESS, ERROR_MESSAGE)
                VALUES (ACC_ERP_REPT_SUCC_SEQ.NEXTVAL, :wono, :packid, :partno,
                        :cnt, :line, :schb_number, :source_bill_no,
                        :report_time, :is_success, :error_message)
                """

                # Parse report_time
                report_time_str = record.get('report_time', '')
                report_time = None
                if report_time_str:
                    try:
                        report_time = datetime.fromisoformat(report_time_str)
                    except (ValueError, TypeError):
                        report_time = datetime.utcnow()
                else:
                    report_time = datetime.utcnow()

                cursor.execute(sql, {
                    'schb_number': schb_number,
                    'wono': source_bill_no,
                    'packid': record.get('lot_number', '') or '',
                    'source_bill_no': source_bill_no,
                    'cnt': record.get('qty', 0) or 0,
                    'partno': record.get('product_code', '') or 'UNKNOWN',
                    'line': record.get('line', '') or '',
                    'report_time': report_time,
                    'is_success': 1 if is_success else 0,
                    'error_message': error_message
                })

                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    duplicates += 1

            except cx_Oracle.IntegrityError:
                duplicates += 1
            except cx_Oracle.Error as e:
                errors_list.append(f"{schb_number}: {str(e)[:100]}")
                eai_logger.warning(f"EAI record insert error: {e}, schb={schb_number}")

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        eai_logger.error(f"EAI database connection error for schema {schema}: {e}")
        return jsonify({
            'code': 500,
            'message': f'Database error: {str(e)[:200]}',
            'data': {'inserted': inserted, 'duplicates': duplicates}
        }), 500

    eai_logger.info(f"EAI logs received: schema={schema}, total={len(records)}, "
                    f"inserted={inserted}, duplicates={duplicates}")

    return jsonify({
        'code': 200,
        'message': 'EAI logs processed',
        'data': {
            'inserted': inserted,
            'duplicates': duplicates,
            'total': len(records),
            'errors': errors_list[:5] if errors_list else []
        }
    })


@api_bp.route('/agent/test', methods=['POST'])
def test_agent_report():
    """
    Test endpoint to simulate agent report for local testing
    Useful when real agents cannot connect
    """
    data = request.get_json() or {}

    server_id = data.get('server_id', 'test')

    # Generate test data
    import random
    test_data = {
        'server_id': server_id,
        'hostname': data.get('hostname', f'TEST-{server_id}'),
        'timestamp': datetime.utcnow().isoformat(),
        'resources': {
            'cpu_usage': data.get('cpu', random.randint(10, 50)),
            'memory_usage': data.get('memory', random.randint(30, 70)),
            'disk_usage': data.get('disk', random.randint(40, 80))
        },
        'processes': data.get('processes', [
            {'name': 'Pack.Server', 'status': 'running', 'pid': 1234, 'cpu': 5.2, 'memory': 128},
            {'name': 'ACC.Server', 'status': 'running', 'pid': 1235, 'cpu': 3.1, 'memory': 256},
            {'name': 'ACC.MQ', 'status': 'running', 'pid': 1236, 'cpu': 1.5, 'memory': 64},
            {'name': 'Oracle', 'status': 'running', 'pid': 1237, 'cpu': 12.3, 'memory': 512}
        ]),
        'alerts': []
    }

    # Store the test data
    agent_data_service.update_agent_data(server_id, test_data)

    return jsonify({
        'code': 200,
        'message': 'Test report stored',
        'data': test_data
    })


# ============ Health Check ============

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'code': 200,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })
