from pyspark.sql import SparkSession
from pyspark.sql.functions import expr


# ---------------------------------------------------
# Example 1: Spark Streaming Application: File Source
# ---------------------------------------------------


spark = SparkSession \
    .builder \
    .appName("File Streaming Demo") \
    .master("local[3]") \
    .config("spark.streaming.stopGracefullyOnShutdown", "true") \
    .config("spark.sql.streaming.schemaInference", "true") \
    .getOrCreate()

# READ
raw_df = spark.readStream \
    .format("json") \
    .option("path", "source") \
    .option("maxFilesPerTrigger", 1) \
    .option("cleanSource", "archive") \
    .option("sourceArchiveDir", "archive-dir") \
    .load()


# TRANFORM
explode_df = raw_df.selectExpr("InvoiceNumber", "CreatedTime", "StoreID", "PosID",
                                "CustomerType", "PaymentMethod", "DeliveryType", "DeliveryAddress.City",
                                "DeliveryAddress.State",
                                "DeliveryAddress.PinCode", 
                                "explode(InvoiceLineItems) as LineItem")

flattened_df = explode_df \
.withColumn("ItemCode", expr("LineItem.ItemCode")) \
.withColumn("ItemDescription", expr("LineItem.ItemDescription")) \
.withColumn("ItemPrice", expr("LineItem.ItemPrice")) \
.withColumn("ItemQty", expr("LineItem.ItemQty")) \
.withColumn("TotalValue", expr("LineItem.TotalValue")) \
.drop("LineItem")


# WRITE
invoiceWriterQuery = flattened_df.writeStream \
    .format("json") \
    .queryName("Flattened Invoice Writer") \
    .outputMode("append") \
    .option("path", "sink/flattened-invoices") \
    .option("checkpointLocation", "chk-point-dir") \
    .trigger(processingTime="1 minute") \
    .start()



invoiceWriterQuery.awaitTermination()