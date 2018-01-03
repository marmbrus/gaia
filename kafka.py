import json
import logging
import time
from dateutil.parser import parse

from subprocess import call
from os.path import expanduser

from confluent_kafka import Producer
from confluent_kafka import Consumer, KafkaError, TopicPartition

config = {'bootstrap.servers': 'localhost'}
logger = logging.getLogger("kafka")
bindir = expanduser("~/confluent-4.0.0/bin")

class KafkaStore:
    def write(self, data):
        p = Producer(config)
        for record in data:
            p.produce("sensor-" + record["sensor"], json.dumps(record).encode('utf-8'))
        p.flush()

def delete_topic(topic):
    ret = call(["{bin}/kafka-topics".format(bin=bindir), "--zookeeper",  "localhost", "--delete", "--topic", topic])
    logger.warning(ret)

def dump_topics(topics, maxage):
    c = Consumer({'bootstrap.servers': 'localhost',
                  'group.id': 'webrequest2',
                  'default.topic.config': {'auto.offset.reset': 'earliest'}})
    messages = []
    for t in topics:
        partitions = [TopicPartition(t, 0, -2)]
        c.assign(partitions)
        running = True
        while running:
            msg = c.poll(timeout=100)
            if msg:
                data = json.loads(msg.value().decode("utf8"))
                if "timestamp" not in data:
                    "Skip"
                elif not maxage or maxage < parse(data["timestamp"], fuzzy=True):
                    messages.append(data)
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
            logger.info("Emitting to {topic}".format(topic=msg.topic()))
            socket.emit(msg.topic(), data)
