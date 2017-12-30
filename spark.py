from os.path import expanduser

from pyspark.sql import SparkSession

spark = SparkSession\
    .builder\
    .appName("gaia")\
    .getOrCreate()

def topic(t):
    return spark.readStream \
        .format("org.apache.spark.sql.kafka010.KafkaSourceProvider") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", t) \
        .option("startingOffsets", "earliest") \
        .load()

def stream(name):
    def stream_dec(func):
        df = func()
        df.writeStream \
          .format("org.apache.spark.sql.kafka010.KafkaSourceProvider") \
          .option("kafka.bootstrap.servers", "localhost:9092") \
          .option("topic", name) \
          .option("checkpointLocation", expanduser("~/checkpoints/{name}".format(name=name))) \
          .start()
        return func
    return stream_dec
    
@stream("historical")
def balcony_historical():
    return topic("sensor-balcony")
    
spark.streams.awaitAnyTermination()