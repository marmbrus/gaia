from localstore import *
from web import app, socketio
from scheduler import get_scheduler, read_and_publish
from sensors import *

import logging
import requests

import hmac
import hashlib

sensors = [
    #OneWireSensor("1", "28-0516a1891dff"),
    #OneWireSensor("2", "28-0516a1b966ff"),
    TempHumidity("sht10", 23, 24),
#    DHT22("dht", 27),
    #FakeSensor("fake1"),
    #FakeSensor("fake2"),
    OpenScale('/dev/ttyUSB1')
]

if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    logger = logging.getLogger("main")
    
    while True:
        readings = []
        for s in sensors:
            try:
                reading = s.read()
                logger.info("{sensor} returned reading {reading}".format(sensor=reading["sensor"], reading=str(reading)[0:20]))
                serialized = json.dumps(reading)
                auth = hmac.new("G414asl2%3d", serialized, hashlib.sha1).hexdigest()
                headers = {'Content-type': 'application/json', 'Authorization': auth}
                r = requests.put("http://gaia.bio/record", data=serialized, headers=headers)
                print(r.status_code)
            except:
                print("error")
        time.sleep(60)
    