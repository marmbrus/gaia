from datetime import timedelta
import time
import json

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

from flask_socketio import SocketIO

from kafka import dump_topics

app = Flask("gaia-web")
socketio = SocketIO(app)

def uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return str(timedelta(seconds = uptime_seconds))

@app.route("/")
def index():
    # publish_reading()
    graphs = [
        {
            "title": "outside temperature",
            "data": ["sensor-balcony"],
            "x": "timestamp",
            "y": "temp_f"
        },
        {
            "title": "random data",
            "data": ["sensor-fake1", "sensor-fake2"],
            "series": "sensor",
            "x": "timestamp",
            "y": "value"
        },
    ]
    return render_template('graphs.html', uptime=uptime(), graphs=graphs)

@app.route("/stream")
def stream():
    topics = request.args.get('topics', [])
    if topics:
        topics = topics.split(",")
    data = dump_topics(topics)
    return jsonify(data)