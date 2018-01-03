from datetime import timedelta
from datetime import datetime
import parsedatetime
import pytz

import os
import time
import json

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import send_from_directory

from flask_socketio import SocketIO

from kafka import dump_topics

app = Flask("gaia-web")
socketio = SocketIO(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
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
            "y": "temp_f",
            "age": "1 day"
        },
        {
            "title": "inside temperature",
            "data": ["sensor-sht10", "sensor-dht"],
            "series": "sensor",
            "x": "timestamp",
            "y": "temperature_f",
            "age": "1 hour"
        },
        {
            "title": "inside humidity",
            "data": ["sensor-sht10"],
            "series": "sensor",
            "x": "timestamp",
            "y": "humidity",
            "age": "1 hour"
        },
    ]
    return render_template('graphs.html', uptime=uptime(), graphs=graphs)

@app.route("/stream")
def stream():
    topics = request.args.get('topics', [])
    if topics:
        topics = topics.split(",")
    maxage = request.args.get('age', None)
    if maxage:
        diff = parsedatetime.Calendar().parseDT(maxage, sourceTime=datetime.min)[0] - datetime.min
        maxage = datetime.now(pytz.timezone('US/Pacific')) - diff
    data = dump_topics(topics, maxage)
    return jsonify(data)