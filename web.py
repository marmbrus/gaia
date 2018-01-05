from datetime import timedelta
from datetime import datetime
import parsedatetime
import pytz
import logging
import hmac
import hashlib

import os
import time
import json

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import send_from_directory
from flask import Response

from flask_socketio import SocketIO

from kafka import dump_topics, kafkaStore
from sensors import c2f

app = Flask("gaia-web")
socketio = SocketIO(app)
logger = logging.getLogger("web")

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
            "data": ["sensor-sht10", "sensor-dht", "sensor-40255102185161225227", "sensor-4025529137161225182"],
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
        
        {
            "title": "light",
            "data": ["sensor-tsl2561"],
            "x": "timestamp",
            "y": "lux",
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

@app.route('/record', methods=['PUT'])
def record():
    content = request.json
    auth = request.headers["Authorization"]
    expected = hmac.new("G414asl2%3d", request.data, hashlib.sha1).hexdigest()
    if auth != expected:
        return Response('Invalid Authorization Header', 401)
    ts = content["sec"] + content["usec"] / 1000000
    content["timestamp"] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S -0000')
    content["sensor"] = content["sensor"].replace(":", "")
    if "temperature_f" in content:
        content["temperature_f"] = c2f(content["temperature_c"])
    logger.info("PUT: {content}".format(content=content))
    kafkaStore.write([content])
    return "OK"