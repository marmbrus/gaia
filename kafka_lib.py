import json
import logging
import time
from dateutil.parser import parse
from datetime import datetime

from subprocess import call
from os.path import expanduser

from confluent_kafka import Producer
from confluent_kafka import Consumer, KafkaError, TopicPartition

from kafka import KafkaConsumer

import pytz

config = {'bootstrap.servers': 'localhost'}
logger = logging.getLogger("kafka")
bindir = expanduser("~/confluent-4.0.0/bin")

class KafkaStore:
    def write(self, data):
        p = Producer(config)
        for record in data:
            p.produce("sensor-" + record["sensor"], json.dumps(record).encode('utf-8'))
        p.flush()
        
kafkaStore = KafkaStore()

def compact_topic(topic):
    ret = call(["{bin}/kafka-topics".format(bin=bindir), "--zookeeper", "localhost:2181", "--alter", "--topic", topic, "--config", "cleanup.policy=compact"])
    logger.warning(ret)

def delete_topic(topic):
    ret = call(["{bin}/kafka-topics".format(bin=bindir), "--zookeeper",  "localhost", "--delete", "--topic", topic])
    logger.warning(ret)

def dump_topics(topics, maxage):
    c = Consumer({'bootstrap.servers': 'localhost',
                  'group.id': 'webrequest2',
                  'default.topic.config': {'auto.offset.reset': 'earliest'}})
    c2 = KafkaConsumer()
                  
    messages = {}
    noDedup = []
    for t in topics:
        tp = TopicPartition(t, 0)
        epoch_age = (maxage - datetime(1970,1,1).replace(tzinfo=pytz.utc)).total_seconds() * 1000
        offsets = c2.offsets_for_times({tp: epoch_age})
        offset = [v for v in offsets.values() if v][0][0]
        logger.info("Skipping to {offset}".format(offset=offset))
        partitions = [TopicPartition(t, 0, offset)]
        c.assign(partitions)
        running = True
        while running:
            msg = c.poll(timeout=100)
            if msg:
                data = json.loads(msg.value().decode("utf8"))
                if "timestamp" not in data:
                    "Skip"
                elif not maxage or maxage < parse(data["timestamp"], fuzzy=True):
                    key = msg.key()
                    if key:
                        data["key"] = key.decode("utf8")
                        messages[key] = data
                    else:
                        noDedup.append(data)
            else:
                running = False
    c.close()
    return messages.values() + noDedup
    
def poll_topic(socket, topics):
    c = Consumer({'bootstrap.servers': 'localhost',
                  'group.id': 'webpoll2',
                  'default.topic.config': {'auto.offset.reset': 'latest'}})
    c.subscribe(topics)
    while True:
        msg = c.poll(timeout=100)
        if msg:
            data = json.loads(msg.value().decode("utf8"))
            logger.info("Emitting to {topic}".format(topic=msg.topic()))
            socket.emit(msg.topic(), data)
