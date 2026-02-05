# -*- coding: utf-8 -*-
"""
ACC Monitor - Application Entry Point
"""
import os
import sys

# Check Python version for eventlet compatibility
python_version = sys.version_info
use_eventlet = python_version < (3, 12)

if use_eventlet:
    try:
        import eventlet
        eventlet.monkey_patch()
        async_mode = 'eventlet'
    except ImportError:
        async_mode = 'threading'
else:
    # Python 3.12+ doesn't work well with eventlet
    async_mode = 'threading'

from app import create_app, socketio
from app.utils.scheduler import scheduler

# Create application
app = create_app()

# Initialize scheduler but don't start it yet (start manually after testing)
# scheduler.init_app(app)
# with app.app_context():
#     scheduler.start()
print("Scheduler disabled for testing")


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5002))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'

    print(f"""
    ==================================================================
    |           ACC Monitor System - Backend Server                   |
    ==================================================================
    |  Server: http://{host}:{port}
    |  API Docs: http://{host}:{port}/api/health
    |  WebSocket: ws://{host}:{port}/socket.io
    |  Async Mode: {async_mode}
    ==================================================================
    |  Press Ctrl+C to stop the server                               |
    ==================================================================
    """)

    # Run with SocketIO
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=False,  # Disable reloader to avoid issues
        allow_unsafe_werkzeug=True
    )
