from pyspark.sql import SparkSession
from src.transformation.transform import transform_to_gold

def gold_layer_execution(year: int, month: int, day: int):
    spark = SparkSession.builder.appName("gold_layer_execution").getOrCreate()

    # Read Silver data (union of all event types for the given day)
    base_path = f"adls://duongbambo.dfs.core.windows.net/githubarchive/silver"
    silver_path = f"{base_path}/*/{year}/{month:02d}/{day:02d}"
    
    df_silver = spark.read.parquet(silver_path)

    # Perform transformation
    gold_tables = transform_to_gold(df_silver)

    # Write Gold tables
    gold_base_path = f"adls://duongbambo.dfs.core.windows.net/githubarchive/gold"
    
    for table_name, df in gold_tables.items():
        output_path = f"{gold_base_path}/{table_name}/{year}/{month:02d}/{day:02d}"
        df.write.mode("overwrite").parquet(output_path)
        print(f"✅ Wrote Gold table: {table_name}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day",   type=int)
    args = parser.parse_args()

    gold_layer_execution(args.year, args.month, args.day)