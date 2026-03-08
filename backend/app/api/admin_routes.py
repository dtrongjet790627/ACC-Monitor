# -*- coding: utf-8 -*-
"""
ACC Monitor - Admin API Routes
Backend management for servers and services configuration.
"""
import copy
from datetime import datetime
from flask import request, jsonify
from app.api import api_bp
from config.settings import (
    SERVERS, ORACLE_CONFIGS,
    save_servers_to_json, reload_servers
)


def _get_next_server_id():
    """Generate next available server ID (numeric string)"""
    existing_ids = [int(k) for k in SERVERS.keys() if k.isdigit()]
    if not existing_ids:
        return '100'
    return str(max(existing_ids) + 1)


def _get_next_sort_order():
    """Get next sort order value"""
    if not SERVERS:
        return 1
    max_order = max(s.get('sort_order', 0) for s in SERVERS.values())
    return max_order + 1


# ============ Admin Server CRUD API ============

@api_bp.route('/admin/servers', methods=['GET'])
def admin_get_servers():
    """Get all server configurations for admin management"""
    servers_list = []
    for server_id, config in SERVERS.items():
        server_data = {
            'id': server_id,
            **config,
            'service_count': len(config.get('services', [])) + len(config.get('containers', [])),
            'has_oracle_config': server_id in ORACLE_CONFIGS
        }
        servers_list.append(server_data)

    # Sort by sort_order
    servers_list.sort(key=lambda x: x.get('sort_order', 999))

    return jsonify({
        'code': 200,
        'data': servers_list,
        'total': len(servers_list)
    })


@api_bp.route('/admin/servers', methods=['POST'])
def admin_create_server():
    """Create a new server configuration"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': 'No data provided'}), 400

    # Validate required fields
    required_fields = ['name', 'ip', 'os']
    for field in required_fields:
        if field not in data:
            return jsonify({'code': 400, 'message': f'Missing required field: {field}'}), 400

    # Use provided ID or generate one
    server_id = data.get('id') or _get_next_server_id()

    if server_id in SERVERS:
        return jsonify({'code': 409, 'message': f'Server ID {server_id} already exists'}), 409

    # Build server config
    server_config = {
        'name': data['name'],
        'name_cn': data.get('name_cn', ''),
        'ip': data['ip'],
        'os': data['os'],
        'log_path': data.get('log_path', ''),
        'processes': data.get('processes', []),
        'services': data.get('services', []),
        'has_oracle': data.get('has_oracle', False),
        'sort_order': data.get('sort_order', _get_next_sort_order()),
        'visible': data.get('visible', True)
    }

    # Windows-specific fields
    if data['os'] == 'windows':
        server_config['acc_drive'] = data.get('acc_drive', 'C')

    # Linux-specific fields
    if data['os'] == 'linux':
        server_config['containers'] = data.get('containers', [])
        server_config['container_metrics'] = data.get('container_metrics', False)
        server_config['monitored_metrics'] = data.get('monitored_metrics', [])

    # Optional Oracle config
    if data.get('has_oracle') and data.get('oracle_config'):
        oracle_cfg = data['oracle_config']
        server_config['oracle_type'] = oracle_cfg.get('oracle_type', '')

    SERVERS[server_id] = server_config

    # Handle Oracle config
    if data.get('has_oracle') and data.get('oracle_config'):
        oc = data['oracle_config']
        ORACLE_CONFIGS[server_id] = {
            'host': data['ip'],
            'port': oc.get('port', 1521),
            'service_name': oc.get('service_name', 'ACC_DB'),
            'username': oc.get('username', 'ACC'),
            'tablespaces': oc.get('tablespaces', ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM'])
        }

    # Persist to JSON
    if not save_servers_to_json(SERVERS, ORACLE_CONFIGS):
        return jsonify({'code': 500, 'message': 'Failed to save configuration'}), 500

    return jsonify({
        'code': 200,
        'message': 'Server created successfully',
        'data': {'id': server_id, **server_config}
    })


@api_bp.route('/admin/servers/<server_id>', methods=['GET'])
def admin_get_server(server_id):
    """Get single server configuration details"""
    if server_id not in SERVERS:
        return jsonify({'code': 404, 'message': f'Server {server_id} not found'}), 404

    config = SERVERS[server_id]
    oracle_config = ORACLE_CONFIGS.get(server_id)

    return jsonify({
        'code': 200,
        'data': {
            'id': server_id,
            **config,
            'oracle_config': oracle_config
        }
    })


@api_bp.route('/admin/servers/<server_id>', methods=['PUT'])
def admin_update_server(server_id):
    """Update server configuration"""
    if server_id not in SERVERS:
        return jsonify({'code': 404, 'message': f'Server {server_id} not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': 'No data provided'}), 400

    current = SERVERS[server_id]

    # Update allowed fields
    updatable_fields = [
        'name', 'name_cn', 'ip', 'os', 'acc_drive', 'log_path',
        'processes', 'services', 'has_oracle', 'sort_order', 'visible',
        'containers', 'container_metrics', 'monitored_metrics', 'oracle_type'
    ]

    for field in updatable_fields:
        if field in data:
            current[field] = data[field]

    SERVERS[server_id] = current

    # Update Oracle config if provided
    if data.get('oracle_config') is not None:
        if data.get('has_oracle', current.get('has_oracle')):
            oc = data['oracle_config']
            ORACLE_CONFIGS[server_id] = {
                'host': data.get('ip', current.get('ip', '')),
                'port': oc.get('port', 1521),
                'service_name': oc.get('service_name', 'ACC_DB'),
                'username': oc.get('username', 'ACC'),
                'tablespaces': oc.get('tablespaces', ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM'])
            }
        else:
            # Remove Oracle config if has_oracle is False
            ORACLE_CONFIGS.pop(server_id, None)

    # Persist to JSON
    if not save_servers_to_json(SERVERS, ORACLE_CONFIGS):
        return jsonify({'code': 500, 'message': 'Failed to save configuration'}), 500

    return jsonify({
        'code': 200,
        'message': 'Server updated successfully',
        'data': {'id': server_id, **SERVERS[server_id]}
    })


@api_bp.route('/admin/servers/<server_id>', methods=['DELETE'])
def admin_delete_server(server_id):
    """Delete a server configuration"""
    if server_id not in SERVERS:
        return jsonify({'code': 404, 'message': f'Server {server_id} not found'}), 404

    server_name = SERVERS[server_id].get('name', server_id)
    del SERVERS[server_id]
    ORACLE_CONFIGS.pop(server_id, None)

    # Persist to JSON
    if not save_servers_to_json(SERVERS, ORACLE_CONFIGS):
        return jsonify({'code': 500, 'message': 'Failed to save configuration'}), 500

    return jsonify({
        'code': 200,
        'message': f'Server {server_name} deleted successfully'
    })


# ============ Admin Service Management API ============

@api_bp.route('/admin/servers/<server_id>/services', methods=['GET'])
def admin_get_services(server_id):
    """Get all services/containers for a server"""
    if server_id not in SERVERS:
        return jsonify({'code': 404, 'message': f'Server {server_id} not found'}), 404

    config = SERVERS[server_id]
    os_type = config.get('os', 'windows')

    if os_type == 'linux':
        items = config.get('containers', [])
        item_type = 'container'
    else:
        items = config.get('services', [])
        item_type = 'service'

    return jsonify({
        'code': 200,
        'data': {
            'server_id': server_id,
            'os_type': os_type,
            'type': item_type,
            'items': items,
            'processes': config.get('processes', [])
        }
    })


@api_bp.route('/admin/servers/<server_id>/services', methods=['PUT'])
def admin_update_services(server_id):
    """Update services/containers list for a server"""
    if server_id not in SERVERS:
        return jsonify({'code': 404, 'message': f'Server {server_id} not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': 'No data provided'}), 400

    config = SERVERS[server_id]
    os_type = config.get('os', 'windows')

    if 'services' in data and os_type == 'windows':
        config['services'] = data['services']

    if 'containers' in data and os_type == 'linux':
        config['containers'] = data['containers']

    if 'monitored_metrics' in data and os_type == 'linux':
        config['monitored_metrics'] = data['monitored_metrics']

    if 'processes' in data:
        config['processes'] = data['processes']

    SERVERS[server_id] = config

    # Persist to JSON
    if not save_servers_to_json(SERVERS, ORACLE_CONFIGS):
        return jsonify({'code': 500, 'message': 'Failed to save configuration'}), 500

    return jsonify({
        'code': 200,
        'message': 'Services updated successfully',
        'data': {
            'server_id': server_id,
            'services': config.get('services', []),
            'containers': config.get('containers', []),
            'processes': config.get('processes', [])
        }
    })


# ============ Admin Visibility API ============

@api_bp.route('/admin/servers/<server_id>/visibility', methods=['PUT'])
def admin_set_visibility(server_id):
    """Set server visibility on dashboard"""
    if server_id not in SERVERS:
        return jsonify({'code': 404, 'message': f'Server {server_id} not found'}), 404

    data = request.get_json()
    if data is None or 'visible' not in data:
        return jsonify({'code': 400, 'message': 'Missing "visible" field'}), 400

    SERVERS[server_id]['visible'] = bool(data['visible'])

    # Persist to JSON
    if not save_servers_to_json(SERVERS, ORACLE_CONFIGS):
        return jsonify({'code': 500, 'message': 'Failed to save configuration'}), 500

    return jsonify({
        'code': 200,
        'message': f'Server {server_id} visibility set to {data["visible"]}',
        'data': {
            'server_id': server_id,
            'visible': SERVERS[server_id]['visible']
        }
    })


# ============ Admin Sort Order API ============

@api_bp.route('/admin/servers/reorder', methods=['PUT'])
def admin_reorder_servers():
    """Update sort order for multiple servers"""
    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({'code': 400, 'message': 'Missing "order" field'}), 400

    order_list = data['order']  # [{"id": "153", "sort_order": 1}, ...]

    for item in order_list:
        sid = item.get('id')
        new_order = item.get('sort_order')
        if sid in SERVERS and new_order is not None:
            SERVERS[sid]['sort_order'] = new_order

    # Persist to JSON
    if not save_servers_to_json(SERVERS, ORACLE_CONFIGS):
        return jsonify({'code': 500, 'message': 'Failed to save configuration'}), 500

    return jsonify({
        'code': 200,
        'message': 'Server order updated successfully'
    })
