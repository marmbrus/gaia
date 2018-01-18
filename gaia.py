import logging

from web import app, socketio

if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    socketio.run(app, host="0.0.0.0", port=5000)
