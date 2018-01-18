import time
import datetime
import json
import pytz

import requests

import google

from sht_sensor import Sht
import Adafruit_DHT

from random import random

import serial

def get_timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S -0000')
    
def c2f(c):
    return c * 9/5 + 32

class OpenScale():
    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(port, 9600, timeout=1)

    def read(self):
        reading = None
        while reading == None:
            self.ser.write(b'0')
            self.ser.flush()
            line = self.ser.readline()
            parts = line.split(",")
            if len(parts) > 1:
                reading = {
                    "timestamp": get_timestamp(),
                    "sensor": "weight",
                    "weight": (float(parts[0]) + (1.27 - -39.75 - 0.25)) * 1000 + 1.6
                }
        print reading
        return reading

class FakeSensor():
    def __init__(self, name):
        self.value = 10
        self.name = name
    def read(self):
        self.value = self.value + random() - .5
        return {"sensor": self.name, "timestamp": get_timestamp(), "value": self.value}

class WeatherUnderground:
    def __init__(self, name, stationId):
        self.stationId = stationId
        self.name = name
        
    def read(self):
        key = "7ddefdd9c23b19ab"
        station = self.stationId
        url = "http://api.wunderground.com/api/{key}/conditions/q/{station}.json".format(
            key=key,
            station=station)
        r = requests.get(url)
        response = r.json()['current_observation']
        response["sensor"] = self.name
        response["timestamp"] = response["observation_time_rfc822"]
        return response

class OneWireSensor:
    def __init__(self, name, id):
        self.name = name
        self.path = "/sys/bus/w1/devices/{id}/w1_slave".format(id=id)
        
    def read(self):
        f = open(self.path, "r")
        lines = f.readlines()
        if lines[0][-4:] != "YES\n":
            return None
        temp = int(lines[1][-6:].strip())
        f.close()
        return {
            "timestamp": get_timestamp(),
            "sensor": self.name, 
            "temperature_c": float(temp) / 1000,
            "temperature_f": c2f(float(temp) / 1000),
        }
        
        
class TempHumidity:
    def __init__(self, name, data, clock):
        self.name = name
        self.sht = Sht(data, clock, voltage="5V")
        
    def read(self):
        temp = self.sht.read_t()
        return {
            "timestamp": get_timestamp(),
            "sensor": self.name, 
            "temperature_c": temp,
            "temperature_f": c2f(temp),
            "humidity": self.sht.read_rh()
        }
        
class DHT22:
    def __init__(self, name, data):
        self.name = name

    def read(self):
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 27)
        return {
            "timestamp": get_timestamp(),
            "sensor": self.name,
            "humidity": humidity,
            "temperature_c": temperature,
            "temperature_f": c2f(temperature)
        }