import atexit

from sensors import get_timestamp

from apscheduler.schedulers.background import BackgroundScheduler

impl = None
impl = BackgroundScheduler()
impl.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: impl.shutdown())

def get_scheduler():
    return impl
    
def read_and_publish(sensors, stores):
    ts = get_timestamp()
    readings = [s.read() for s in sensors]
    for reading in readings:
        reading["timestamp"] = ts
        print(reading)
    for store in stores:
        store.write(readings)