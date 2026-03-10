# -*- coding: utf-8 -*-
"""
ACC Monitor - Application Factory
"""
import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()


def _migrate_tablespace_columns(app):
    """Add current_file_* columns to ops_tablespace_data if they don't exist (SQLite migration)."""
    import sqlite3
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_path.startswith('sqlite:///'):
        return
    db_file = db_path.replace('sqlite:///', '')
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.execute("PRAGMA table_info(ops_tablespace_data)")
        columns = [row[1] for row in cursor.fetchall()]
        new_cols = {
            'current_file_pct': 'FLOAT',
            'current_file_used_mb': 'FLOAT',
            'current_file_max_mb': 'FLOAT',
        }
        for col_name, col_type in new_cols.items():
            if col_name not in columns:
                conn.execute(f"ALTER TABLE ops_tablespace_data ADD COLUMN {col_name} {col_type}")
                app.logger.info("Migration: added column %s to ops_tablespace_data", col_name)
        conn.commit()
        conn.close()
    except Exception as e:
        app.logger.warning("Migration check failed (non-critical): %s", e)


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)

    # Load configuration
    from config.settings import config
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(app.root_path), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    CORS(app)

    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register Oracle Ops blueprint
    from app.api.oracle_ops_routes import oracle_ops_bp
    app.register_blueprint(oracle_ops_bp, url_prefix='/api/oracle-ops')

    # Create database tables (import oracle_ops_models to register them)
    from app.models import oracle_ops_models  # noqa: F401
    with app.app_context():
        db.create_all()
        # Migrate: add current_file columns to ops_tablespace_data if missing
        _migrate_tablespace_columns(app)
        # Ensure performance indexes exist on Oracle Ops tables
        from app.services.oracle_ops_service import oracle_ops_service
        oracle_ops_service.ensure_indexes()
        # Clean up old data to prevent database bloat (keep 7 days tablespace, 30 days alerts)
        oracle_ops_service.cleanup_old_data(days=7)

    # Register WebSocket handlers
    from app.api import websocket

    # Serve frontend static files from ../frontend/dist
    frontend_dist = os.path.join(os.path.dirname(app.root_path), '..', 'frontend', 'dist')
    frontend_dist = os.path.abspath(frontend_dist)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve Vue.js frontend from dist directory"""
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, 'index.html')

    return app
