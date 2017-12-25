import json
import time
import datetime
import threading
from datetime import timedelta
from random import *

import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import httplib2
import requests

from oauth2client.service_account import ServiceAccountCredentials
from apiclient import discovery

from flask import Flask
from flask import render_template
from flask import jsonify

spreadsheet_id = "1AwqAZzx9BEY85W05wn6s8A6cl3pxsZLNyrq8yQ9LLKE"
last_reading=None
app = Flask(__name__)

def get_credentials():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/pi/.credentials/gaia.json', scopes)
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    return discovery.build('sheets', 'v4', http=http,
                           discoveryServiceUrl=discoveryUrl)

def publish_gsheets(reading):
    ts = time.time()
    time_string = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    last_reading = [
        reading["local_time_rfc822"][:-5],
        reading["temp_f"],
        reading["relative_humidity"],
        reading["wind_gust_mph"]
    ]

    service = get_credentials()
    request = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Measurements!A:A",
        valueInputOption="USER_ENTERED",
        body={
            "majorDimension": "ROWS",
            "values": [last_reading]
        })
    response = request.execute()
    print(response)

def fetchWeather():
    key = "7ddefdd9c23b19ab"
    station = "pws:KCABERKE86"
    url = "http://api.wunderground.com/api/{key}/conditions/q/{station}.json".format(
            key=key,
            station=station)
    r = requests.get(url)
    response = r.json()['current_observation']
    return response

def uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return str(timedelta(seconds = uptime_seconds))

@app.route("/")
def index():
    # publish_reading()
    return render_template('index.html', uptime=uptime())

@app.route("/weather")
def weather():
    return jsonify(fetchWeather())

@app.route("/report")
def report():
    publish_gsheets(fetchWeather())
    return "okay"

@app.route("/sensor/<name>")
def sensor(name):
    data = []
    with open("/home/pi/gaia/static/weather.json", "r") as file:
        for line in file.readlines():
            data.append(json.loads(line))
    return jsonify(data)


@app.before_first_request
def initialize():
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=lambda: publish_gsheets(fetchWeather()),
        trigger=IntervalTrigger(minutes=10),
        id='weather',
        name='Fetching Weather',
        replace_existing=True)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
