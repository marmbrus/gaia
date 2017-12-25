import time
import datetime
import json

import requests

import google

from sht_sensor import Sht

def timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

class WeatherUnderground:
    def __init__(self, stationId):
        self.stationId = stationId
        
    def read(self):
        key = "7ddefdd9c23b19ab"
        station = self.stationId
        url = "http://api.wunderground.com/api/{key}/conditions/q/{station}.json".format(
            key=key,
            station=station)
        r = requests.get(url)
        response = r.json()['current_observation']
        response["name"] = self.stationId
        return response

class OneWireSensor:
    def __init__(self, name, id):
        self.name = name
        self.path = "/sys/bus/w1/devices/{id}/w1_slave".format(id=id)
        
    def read(self):
        f = open(self.path, "r")
        lines = f.readlines()
        if lines[0][-4:] != "YES\n":
            print(lines)
            return None
        temp = int(lines[1][-6:].strip())
        f.close()
        return {
            "name": self.name, 
            "temp": float(temp) / 1000
        }
        
        
class TempHumidity:
    def __init__(self, name, data, clock):
        self.name = name
        self.sht = Sht(data, clock, voltage="5V")
        
    def read(self):
        return {
            "name": self.name, 
            "temp": self.sht.read_t(), 
            "humidity": self.sht.read_rh()
        }

sensors = [
    #OneWireSensor("1", "28-0516a1891dff"),
    #OneWireSensor("2", "28-0516a1b966ff"),
    TempHumidity("3", 23, 24),
    WeatherUnderground("pws:KCABERKE86"),
]

sheet = google.GoogleSheet()

data = open("data.json", "a")

def publish():
    while True:
        ts = timestamp()
        readings = [s.read() for s in sensors]
        for reading in readings:
            reading["timestamp"] = ts
            data.write(json.dumps(reading))
            data.write("\n")
            data.flush()
            #sheet.publish(reading)
            print(reading)
            
        time.sleep(30)
        
publish()