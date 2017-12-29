import time
import datetime
import json

import requests

import google

from sht_sensor import Sht
import Adafruit_DHT

def get_timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    
def c2f(c):
    return c * 9/5 + 32

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
            "sensor": self.name,
            "humidity": humidity,
            "temperature_c": temperature,
            "temperature_f": c2f(temperature)
        }