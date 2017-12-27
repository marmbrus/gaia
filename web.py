from datetime import timedelta
import time
import json

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

from confluent_kafka import Consumer, KafkaError, TopicPartition

app = Flask("gaia-web")

def uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return str(timedelta(seconds = uptime_seconds))

@app.route("/")
def index():
    # publish_reading()
    return render_template('index.html', uptime=uptime())

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
    c = Consumer({'bootstrap.servers': 'localhost',
                  'group.id': 'webrequest',
                  'default.topic.config': {'auto.offset.reset': 'earliest'}})
    messages = []
    
    for s in sensors:
        partitions = [TopicPartition("sensor-" + s, 0, -2)]
        c.assign(partitions)
        running = True
        while running:
            msg = c.poll(timeout=100)
            if msg:
                messages.append(json.loads(msg.value().decode("utf8")))
            else:
                running = False
    c.close()
    return jsonify(messages)