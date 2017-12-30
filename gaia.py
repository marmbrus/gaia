from localstore import *
from web import app, socketio
from scheduler import get_scheduler, read_and_publish
from sensors import *
from kafka import *

from apscheduler.triggers.interval import IntervalTrigger

from thread import start_new_thread

inside = [
    #OneWireSensor("1", "28-0516a1891dff"),
    #OneWireSensor("2", "28-0516a1b966ff"),
    #TempHumidity("sht10", 23, 24),
    #DHT22("dht", 27),
    FakeSensor("fake1")
]
    
outside = [
    WeatherUnderground("balcony", "pws:KCABERKE86"),
]

stores = [
    LocalStore("data.json"),
    KafkaStore()
]

@app.before_first_request
def init():
    get_scheduler().add_job(
        func=lambda: read_and_publish(outside, stores),
        trigger=IntervalTrigger(minutes=5),
        id='outside',
        name='outside fetcher',
        replace_existing=True)
        
    get_scheduler().add_job(
        func=lambda: read_and_publish(inside, stores),
        trigger=IntervalTrigger(seconds=10),
        id='inside',
        name='inside fetcher',
        replace_existing=True)

    start_new_thread(poll_topic, (socketio, ["sensor-balcony", "sensor-fake1"]))

if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    read_and_publish(outside, stores)
    read_and_publish(inside , stores)

    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
