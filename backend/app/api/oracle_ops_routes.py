# -*- coding: utf-8 -*-
"""
Oracle Ops - REST API Routes for Oracle Database Operations Monitoring.
Handles both execution agent data reporting and frontend queries.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.oracle_ops_service import oracle_ops_service

oracle_ops_bp = Blueprint('oracle_ops', __name__)


# ============ Agent Report API ============

@oracle_ops_bp.route('/report', methods=['POST'])
def receive_report():
    """
    Receive full report from execution agent.
    Expected JSON payload:
    {
        "server_id": "164",
        "server_name": "ECU Line1",
        "timestamp": "2026-03-07T02:00:05",
        "tablespaces": [...],
        "backups": [...],
        "cleanups": [...],
        "alerts": [...]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': 'No data provided'}), 400

    server_id = data.get('server_id')
    if not server_id:
        return jsonify({'code': 400, 'message': 'server_id is required'}), 400

    try:
        stored = oracle_ops_service.store_report_data(data)
        return jsonify({
            'code': 200,
            'message': 'Report received',
            'server_id': server_id,
            'stored': stored,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to store report: {str(e)}'
        }), 500


# ============ Frontend Query APIs ============

@oracle_ops_bp.route('/overview', methods=['GET'])
def get_overview():
    """
    Get 6-database operations overview.
    Returns status, max tablespace usage, latest backup, recent alerts per server.
    """
    try:
        overview = oracle_ops_service.get_overview()
        return jsonify({
            'code': 200,
            'data': overview,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get overview: {str(e)}'
        }), 500


@oracle_ops_bp.route('/tablespaces', methods=['GET'])
def get_tablespaces():
    """
    Get tablespace details.
    Query params: server_id (optional)
    """
    server_id = request.args.get('server_id')

    try:
        data = oracle_ops_service.get_tablespaces(server_id=server_id)
        return jsonify({
            'code': 200,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get tablespaces: {str(e)}'
        }), 500


@oracle_ops_bp.route('/tablespaces/trends', methods=['GET'])
def get_tablespace_trends():
    """
    Get tablespace usage trend data for ECharts.
    Query params: server_id (optional), days (default 7)
    """
    server_id = request.args.get('server_id')
    days = request.args.get('days', 7, type=int)

    try:
        data = oracle_ops_service.get_tablespace_trends(server_id=server_id, days=days)
        return jsonify({
            'code': 200,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get trends: {str(e)}'
        }), 500


@oracle_ops_bp.route('/backups', methods=['GET'])
def get_backups():
    """
    Get backup execution records.
    Query params: server_id, status, page, page_size
    """
    server_id = request.args.get('server_id')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        data = oracle_ops_service.get_backups(
            server_id=server_id, status=status,
            page=page, page_size=page_size
        )
        return jsonify({
            'code': 200,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get backups: {str(e)}'
        }), 500


@oracle_ops_bp.route('/cleanups', methods=['GET'])
def get_cleanups():
    """
    Get cleanup execution records.
    Query params: server_id, status, page, page_size
    """
    server_id = request.args.get('server_id')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        data = oracle_ops_service.get_cleanups(
            server_id=server_id, status=status,
            page=page, page_size=page_size
        )
        return jsonify({
            'code': 200,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get cleanups: {str(e)}'
        }), 500


@oracle_ops_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get alert history records.
    Query params: server_id, severity, page, page_size
    """
    server_id = request.args.get('server_id')
    severity = request.args.get('severity')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    try:
        data = oracle_ops_service.get_alerts(
            server_id=server_id, severity=severity,
            page=page, page_size=page_size
        )
        return jsonify({
            'code': 200,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get alerts: {str(e)}'
        }), 500


# ============ Configuration APIs ============

@oracle_ops_bp.route('/config/<server_id>', methods=['GET'])
def get_config(server_id):
    """Get current configuration from an execution agent"""
    try:
        config = oracle_ops_service.get_agent_config(server_id)
        if config is None:
            return jsonify({
                'code': 404,
                'message': f'Unknown server: {server_id}'
            }), 404

        return jsonify({
            'code': 200,
            'data': config,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get config: {str(e)}'
        }), 500


@oracle_ops_bp.route('/config/<server_id>', methods=['POST'])
def push_config(server_id):
    """Push configuration to an execution agent"""
    config_data = request.get_json()
    if not config_data:
        return jsonify({'code': 400, 'message': 'No config data provided'}), 400

    try:
        result = oracle_ops_service.push_agent_config(server_id, config_data)
        status_code = 200 if result.get('success') else 500
        return jsonify({
            'code': status_code,
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        }), status_code
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to push config: {str(e)}'
        }), 500
