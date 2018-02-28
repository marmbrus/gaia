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

from kafka_lib import dump_topics, kafkaStore, poll_topic
from sensors import c2f

from sets import Set
from thread import start_new_thread


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
    graphs = []
    with open('graphs.json') as json_data:
        graphs = json.load(json_data)
    for graph in graphs:
        graph["title"] = graph["title"]
        graph["age"] = "2 hours"

    for graph in graphs[:]:
        print(graph)
        windowed = graph.copy()
        windowed["title"] = graph["title"] + " - 10 days"
        windowed["age"] = "10 days"
        windowed["data"] = [d + "-10min" for d in windowed["data"]]
        graphs.append(windowed)
        
    return render_template('graphs.html', uptime=uptime(), graphs=graphs)

listeners = Set()

@app.route("/stream")
def stream():
    topics = request.args.get('topics', [])
    if topics:
        topics = topics.split(",")
        
    for t in topics:
        if t not in listeners:
            listeners.add(t)
            start_new_thread(poll_topic, (socketio, [t]))
    
    maxage = request.args.get('age', None)
    if maxage:
        diff = parsedatetime.Calendar().parseDT(maxage, sourceTime=datetime.min)[0] - datetime.min
        maxage = datetime.now(pytz.timezone('US/Pacific')) - diff
    data = dump_topics(topics, maxage)
    return jsonify(data)

tags = {
    "68c63a9fb15c": {
        "user": "michael",
        "plant": "ficus"
    },
    "60019473d8a7": {
        "user": "michael",
    },
    "60019473e1bc": {
        "user": "michael"
    },
    "60019474508f": {
        "user": "chris"
    },
    "6001947450b7": {
        "user": "brent"
    },
    "6001947448b8": {
        "user": "michael",
        "plant": "miltonia"
    },
    "60019473da84": {
        "user": "michael",
        "plant": "phal"
    }
}

@app.route('/record', methods=['PUT'])
def record():
    content = request.json
    auth = request.headers["Authorization"]
    expected = hmac.new("G414asl2%3d", request.data, hashlib.sha1).hexdigest()
    if auth != expected:
        return Response('Invalid Authorization Header', 401)
    if "sec" in content:
        ts = content["sec"] + content["usec"] / 1000000
        content["timestamp"] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S -0000')
    content["sensor"] = content["sensor"].replace(":", "")
    if "temperature_c" in content:
        content["temperature_f"] = c2f(content["temperature_c"])
    mac = content["sensor"][0:12]
    print(mac)
    if mac in tags:
        content["tags"] = tags[mac]
    logger.info("PUT: {content}".format(content=content))
    kafkaStore.write([content])
    return "OK"