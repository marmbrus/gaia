import os
import time

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
    schema = (
        StructType() 
            .add("timestamp", StringType())
            .add("sensor", StringType())
            .add("relative_humidity", StringType())
            .add("temperature_f", DoubleType())
            .add("weight", DoubleType())
        )
    return (spark.readStream
        .format("org.apache.spark.sql.kafka010.KafkaSourceProvider")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", t)
        .option("startingOffsets", "earliest")
        .load()
        .select(from_json(col("value").cast("string"), schema).alias("json")) 
        .selectExpr("json.*") 
        .withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
        .withWatermark("timestamp", "10 minutes")
    )
    
def stream(name):
    def stream_dec(func):
        df = func()
        checkpoint = os.path.expanduser("~/checkpoints/{name}".format(name=name))
        
        # This is a new stream, clear out kafka.
        if not os.path.exists(checkpoint):
            delete_topic(name)

        time.sleep(10)
        
        df.withColumn("timestamp", date_format("timestamp", "yyyy-MM-dd HH:mm:ss Z")) \
          .select(to_json(struct(col("*"))).alias("value")) \
          .writeStream \
          .format("org.apache.spark.sql.kafka010.KafkaSourceProvider") \
          .option("kafka.bootstrap.servers", "localhost:9092") \
          .option("topic", name) \
          .option("checkpointLocation", checkpoint) \
          .outputMode("update") \
          .start()
        return func
    return stream_dec

@stream("weights")
def weights():
    return (
        topic("sensor-weight") 
            .withColumn("weight", col("weight") - 1270)
            .groupBy(window(col("timestamp"), "10 minutes").getField("start").alias("timestamp"))
            .agg(avg(col("weight")).alias("weight"))
        )

@stream("temperatures")
def temperatures():
    return (
        topic("sensor-40255102185161225227")
            .union(topic("sensor-4025529137161225182"))
            .union(topic("sensor-sht10"))
            .union(topic("sensor-6001947448b8-dht"))
            .union(topic("sensor-60019474508f-dht"))
        )
        
@stream("temperatures-10min")
def temperatures():
    return (
        temperatures()
            .where(col("temperature_f") > 0)
            .groupBy(window(col("timestamp"), "10 minutes").getField("start").alias("timestamp"), col("sensor"))
            .agg(avg(col("temperature_f")).alias("temperature_f"))
        )

spark.streams.awaitAnyTermination()