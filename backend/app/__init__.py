# -*- coding: utf-8 -*-
"""
ACC Monitor - Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()


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

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register WebSocket handlers
    from app.api import websocket

    return app
