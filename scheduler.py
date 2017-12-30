import atexit
import datetime
import time
import logging

from apscheduler.schedulers.background import BackgroundScheduler

impl = None
impl = BackgroundScheduler()
impl.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: impl.shutdown())

logger = logging.getLogger("scheduler")

def get_scheduler():
    return impl
    
def read_and_publish(sensors, stores):
    readings = []
    for s in sensors:
        reading = s.read()
        logger.info("{sensor} returned reading {reading}".format(sensor=reading["sensor"], reading=str(reading)[0:20]))
        readings.append(reading)
    for store in stores:
        store.write(readings)