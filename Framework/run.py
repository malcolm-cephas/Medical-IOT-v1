from dashboard.app import app, socketio, create_tables
import os

if __name__ == '__main__':
    print("Initializing Database...")
    create_tables()
    print("Starting MediSecure Dashboard...")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
