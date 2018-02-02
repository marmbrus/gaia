import serial
import time

from sensors import get_timestamp
from kafka_lib import kafkaStore

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

while True:
    ser.write(b'0')
    ser.flush()
    reading = ser.readline()
    parts = reading.split(",")
    if len(parts) > 1:
        reading = {
            "timestamp": get_timestamp(),
            "sensor": "weight",
            "weight": (float(parts[0]) + (1.27 - -39.75 - 0.25)) * 1000 + 1.6
        }
        print(reading)
        kafkaStore.write([reading])
        time.sleep(20)
    