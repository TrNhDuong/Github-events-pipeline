from pyspark.sql import SparkSession
from src.transformation.transform import transform_to_gold
from src.core.config_loader import ConfigLoader

def gold_layer_execution(year: int, month: int, day: int):
    spark = SparkSession.builder.appName("gold_layer_execution").getOrCreate()

    loader = ConfigLoader()
    account_config = loader.load("account/account.yml")
    gold_config = loader.load("gold/gold.yml")

    account = account_config["source"]["account"]
    container = account_config["source"]["container"]
    silver_dir = gold_config["source"]["path"]
    gold_dir = gold_config["destination"]["path"]

    # Read Silver data (union of all event types for the given day)
    silver_path = f"abfss://{container}@{account}.dfs.core.windows.net/{silver_dir}/*/{year}/{month:02d}/{day:02d}"
    
    df_silver = spark.read.parquet(silver_path)

    # Perform transformation
    gold_tables = transform_to_gold(df_silver)

    # Write Gold tables
    gold_base_path = f"abfss://{container}@{account}.dfs.core.windows.net/{gold_dir}"
    
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