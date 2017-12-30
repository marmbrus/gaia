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
            "sensors": ["balcony"],
            "x": "timestamp",
            "y": "temp_f"
        },
        {
            "title": "random data",
            "sensors": ["fake1"],
            "x": "timestamp",
            "y": "value"
        },
    ]
    return render_template('graphs.html', uptime=uptime(), graphs=graphs)

@app.route("/data")
def data():
    sensors = request.args.get('sensors', [])
    if sensors:
        sensors = sensors.split(",")

    output_data = []
    files = ["/home/pi/gaia/data.json", "/home/pi/gaia/static/historical.json"]
    for filePath in files:
        with open(filePath, "r") as file:
            for line in file.readlines():
                try:
                    data = json.loads(line)
                    include = True
                    if len(sensors) > 0:
                        if data["sensor"] not in sensors:
                            include = False
                    if include:
                        output_data.append(data)
                except:
                    print(line)
    return jsonify(output_data)

@app.route("/stream")
def stream():
    sensors = request.args.get('sensors', [])
    if sensors:
        sensors = sensors.split(",")
    data = dump_topics(sensors)
    return jsonify(data)