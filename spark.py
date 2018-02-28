import os
import time
import json

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *

from kafka_lib import delete_topic, compact_topic

spark = SparkSession\
    .builder\
    .appName("gaia")\
    .getOrCreate()
    
spark.sql("SET spark.sql.shuffle.partitions=1")

def topic(t, batch = False):
    schema = (
        StructType() 
            .add("timestamp", StringType())
            .add("sensor", StringType())
            .add("relative_humidity", StringType())
            .add("temperature_f", DoubleType())
            .add("temperature_c", DoubleType())
            .add("grams", DoubleType())
            .add("lux", LongType())
            .add("raw", DoubleType())
            .add("stddev", DoubleType())
            .add("tags", MapType(StringType(), StringType()))
        )
    reader = None
    if batch:
      reader = spark.read
    else:
      reader = spark.readStream
    
    return (reader
        .format("org.apache.spark.sql.kafka010.KafkaSourceProvider")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", t)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
        .select(from_json(col("value").cast("string"), schema).alias("json")) 
        .selectExpr("json.*") 
        .withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
        .withWatermark("timestamp", "10 minutes")
    )

graphs = []    
def stream(name, values, keys = []):
    def stream_dec(func):
        df = func()
        checkpoint = os.path.expanduser("~/checkpoints/{name}".format(name=name))
        
        # This is a new stream, clear out kafka.
        if not os.path.exists(checkpoint):
          delete_topic(name)
          time.sleep(10)
          delete_topic(name + "-10min")
          time.sleep(10)
        
        df.withColumn("timestamp", date_format("timestamp", "yyyy-MM-dd HH:mm:ss Z")) \
          .select(to_json(struct(col("*"))).alias("value")) \
          .writeStream \
          .format("org.apache.spark.sql.kafka010.KafkaSourceProvider") \
          .option("kafka.bootstrap.servers", "localhost:9092") \
          .option("topic", name) \
          .option("checkpointLocation", checkpoint) \
          .outputMode("update") \
          .trigger(processingTime="1 minute") \
          .start()
          
        grouping_keys = [col(k) for k in keys]
        aggs = [avg(col(v)).alias(v) for v in values]
        grouping = [window(col("timestamp"), "10 minutes").getField("start").alias("timestamp")] + grouping_keys
        
        compact_topic(name + "-10min")
        df.groupBy(*grouping) \
          .agg(*aggs) \
          .withColumn("timestamp", date_format("timestamp", "yyyy-MM-dd HH:mm:ss Z")) \
          .select( \
            to_json(struct([col("timestamp")] + [col(k) for k in keys])).alias("key"), \
            to_json(struct(col("*"))).alias("value")) \
          .writeStream \
          .format("org.apache.spark.sql.kafka010.KafkaSourceProvider") \
          .option("kafka.bootstrap.servers", "localhost:9092") \
          .option("topic", name + "-10min") \
          .option("checkpointLocation", checkpoint + "-10min") \
          .outputMode("update") \
          .start()
        
        for value in values:
          graph = {
            "title": name,
            "data": [name],
            "series": "sensor",
            "x": "timestamp",
            "y": value
          }
          graphs.append(graph)
          
        return func
    return stream_dec
  
@stream("weights", keys=["sensor"], values=["grams", "stddev"])
def weights():
    return (
          topic("readings")
            .where("grams IS NOT NULL")
            .where("stddev < 200")
            .where("grams < 10000")
            .where("grams > 200")
            .withColumn("sensor", col("tags.plant"))
            .where("NOT (sensor = 'ficus' AND grams > 1800)")
            .where("NOT (sensor = 'plumeria' AND timestamp >= '2017-02-27')")
        )

ranges = (
  topic("weights", batch = True)
    .groupBy("sensor")
    .agg(min("grams").alias("min"), max("grams").alias("max"))
)
ranges.cache()

@stream("water", keys=["sensor"], values=["water"])
def water():
  return (
    weights()
      .join(ranges, ["sensor"])
      .withColumn("water", (col("grams") - col("min")))
    )
    
@stream("water_rel", keys=["sensor"], values=["water"])
def water_rel():
  return (
    weights()
      .join(ranges, ["sensor"])
      .withColumn("water", (col("grams") - col("min")) / (col("max") - col("min")))
    )
  
@stream("evaporation", keys=["sensor"], values=["ml_hour"])
def water_rel():
  spark.sql("SET spark.sql.streaming.unsupportedOperationCheck=false")
  return (
    weights()
      .join(ranges, ["sensor"])
      .groupBy(window("timestamp", "5 minutes").alias("timestamp").getField("end").alias("timestamp"), col("sensor"))
      .agg(((min(struct("timestamp","grams")).getField("grams") - max(struct("timestamp", "grams")).getField("grams"))).alias("ml_hour"))
      .where("ml_hour > 0")
      .where("ml_hour < 30")
    )
  
  
@stream("temperatures", keys = ["sensor"], values = ["temperature_f"])
def temperatures():
    return (
        topic("readings")
          .where("temperature_c != -999")
          .withColumn("sensor", col("tags.user"))
        )

print(graphs)
with open('graphs.json', 'w') as fp:
    json.dump(graphs, fp)

spark.streams.awaitAnyTermination()