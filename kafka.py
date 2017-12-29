import json
import time

from confluent_kafka import Producer
from confluent_kafka import Consumer, KafkaError, TopicPartition

config = {'bootstrap.servers': 'localhost'}

class KafkaStore:
    def write(self, data):
        p = Producer(config)
        for record in data:
            p.produce("sensor-" + record["sensor"], json.dumps(record).encode('utf-8'))
        p.flush()
    
def dump_topics(topics):
    c = Consumer({'bootstrap.servers': 'localhost',
                  'group.id': 'webrequest2',
                  'default.topic.config': {'auto.offset.reset': 'earliest'}})
    messages = []
    for t in topics:
        partitions = [TopicPartition("sensor-" + t, 0, -2)]
        c.assign(partitions)
        running = True
        while running:
            msg = c.poll(timeout=100)
            if msg:
                messages.append(json.loads(msg.value().decode("utf8")))
            else:
                running = False
    c.close()
    return messages
    
def poll_topic(socket, topics):
    c = Consumer({'bootstrap.servers': 'localhost',
                  'group.id': 'webpoll',
                  'default.topic.config': {'auto.offset.reset': 'latest'}})
    c.subscribe(topics)
    while True:
        msg = c.poll(timeout=100)
        if msg:
            data = json.loads(msg.value().decode("utf8"))
            print("emitting")
            socket.emit(msg.topic(), data)
