import os

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *

from kafka import delete_topic

spark = SparkSession\
    .builder\
    .appName("gaia")\
    .getOrCreate()
    
spark.sql("SET spark.sql.shuffle.partitions=1")

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
        checkpoint = os.path.expanduser("~/checkpoints/{name}".format(name=name))
        
        # This is a new stream, clear out kafka.
        if not os.path.exists(checkpoint):
            delete_topic(name)
        
        df.writeStream \
          .format("org.apache.spark.sql.kafka010.KafkaSourceProvider") \
          .option("kafka.bootstrap.servers", "localhost:9092") \
          .option("topic", name) \
          .option("checkpointLocation", checkpoint) \
          .start()
        return func
    return stream_dec
    
@stream("historical")
def balcony_historical():
    return topic("sensor-balcony")
    
@stream("cleaned")
def cleaned():
    strip_percent = udf(lambda x: x[:-1])
    schema = (
        StructType() 
            .add("timestamp", StringType())
            .add("relative_humidity", StringType())
            .add("temp_f", DoubleType())
        )
    return (
        topic("sensor-balcony") 
            .select(from_json(col("value").cast("string"), schema).alias("json")) 
            .selectExpr("json.*") 
            .withColumn("relative_humidity", strip_percent(col("relative_humidity")).cast("double"))
            .dropDuplicates(["timestamp"])
            .select(to_json(struct(col("*"))).alias("value"))
        )

spark.streams.awaitAnyTermination()