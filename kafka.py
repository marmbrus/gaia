import json
from confluent_kafka import Producer

class KafkaStore:
    def write(self, data):
        p = Producer({'bootstrap.servers': 'localhost'})
        for record in data:
            p.produce("sensor-" + record["sensor"], json.dumps(record).encode('utf-8'))
        p.flush()