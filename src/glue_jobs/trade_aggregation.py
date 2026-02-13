"""
trade_aggregation.py - AWS Glue Job for Trade Aggregation

Aggregates trade data by instrument and time period for reporting.

Author: Agnibes Banerjee
License: MIT
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import datetime

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'source_bucket',
    'target_bucket',
    'database_name'
])

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
SOURCE_BUCKET = args['source_bucket']
TARGET_BUCKET = args['target_bucket']
DATABASE_NAME = args['database_name']

print(f"Starting trade aggregation job: {args['JOB_NAME']}")
print(f"Source: s3://{SOURCE_BUCKET}/raw-events/trades/")
print(f"Target: s3://{TARGET_BUCKET}/processed/trade-aggregations/")


def read_trade_events():
    """Read trade events from S3 raw bucket."""
    input_path = f"s3://{SOURCE_BUCKET}/raw-events/trades/"
    
    # Read JSON files
    df = spark.read.json(input_path)
    
    print(f"Read {df.count()} trade events")
    return df


def transform_trades(df):
    """
    Transform and aggregate trade data.
    
    Aggregations:
    - Total volume by instrument and day
    - Average price by instrument and day
    - Trade count by trader
    - High/Low prices
    """
    
    # Convert timestamp to date
    df = df.withColumn(
        'trade_date',
        F.to_date(F.col('timestamp'))
    )
    
    # Daily aggregations by instrument
    daily_agg = df.groupBy('instrument', 'trade_date').agg(
        F.sum('quantity').alias('total_volume'),
        F.avg('price').alias('avg_price'),
        F.max('price').alias('high_price'),
        F.min('price').alias('low_price'),
        F.count('*').alias('trade_count'),
        F.sum(F.when(F.col('direction') == 'BUY', F.col('quantity')).otherwise(0)).alias('buy_volume'),
        F.sum(F.when(F.col('direction') == 'SELL', F.col('quantity')).otherwise(0)).alias('sell_volume')
    )
    
    # Add processing metadata
    daily_agg = daily_agg.withColumn(
        'processed_timestamp',
        F.current_timestamp()
    ).withColumn(
        'processing_date',
        F.current_date()
    )
    
    print(f"Aggregated into {daily_agg.count()} daily summaries")
    return daily_agg


def calculate_trader_metrics(df):
    """Calculate metrics per trader."""
    
    trader_metrics = df.groupBy('trader_id', 'trade_date').agg(
        F.count('*').alias('trades_count'),
        F.sum('quantity').alias('total_quantity'),
        F.sum(F.col('quantity') * F.col('price')).alias('total_value'),
        F.countDistinct('instrument').alias('instruments_traded')
    )
    
    return trader_metrics


def write_aggregations(df, output_name):
    """Write aggregated data to S3 in Parquet format with partitioning."""
    
    output_path = f"s3://{TARGET_BUCKET}/processed/{output_name}/"
    
    # Write partitioned by trade_date
    df.write \
        .mode('overwrite') \
        .partitionBy('trade_date') \
        .parquet(output_path)
    
    print(f"Written {output_name} to {output_path}")


def main():
    """Main ETL workflow."""
    
    # Read source data
    trades_df = read_trade_events()
    
    # Transform and aggregate
    daily_aggregations = transform_trades(trades_df)
    trader_metrics = calculate_trader_metrics(trades_df)
    
    # Write outputs
    write_aggregations(daily_aggregations, 'trade-aggregations')
    write_aggregations(trader_metrics, 'trader-metrics')
    
    # Update Glue Data Catalog
    print("Updating Glue Data Catalog...")
    
    # Register trade-aggregations table
    glueContext.write_dynamic_frame.from_catalog(
        frame=DynamicFrame.fromDF(daily_aggregations, glueContext, "daily_agg"),
        database=DATABASE_NAME,
        table_name="trade_aggregations",
        transformation_ctx="datasink_aggregations"
    )
    
    print("✅ Trade aggregation job completed successfully")


if __name__ == "__main__":
    main()
    job.commit()
