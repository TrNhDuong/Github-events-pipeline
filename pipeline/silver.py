from pyspark.sql import SparkSession 
from pyspark.sql.functions import col 
from functools import reduce
from pyspark.sql import DataFrame
from src.transformation.parse import ParseRegistry
from src.core.config_loader import ConfigLoader

def silver_layer_execution(year: int, month: int, day: int):
    spark = SparkSession.builder.appName("silver_layer_execution").getOrCreate()

    loader = ConfigLoader()
    account_config = loader.load("account/account.yml")
    silver_config = loader.load("silver/silver.yml")

    account = account_config["source"]["account"]
    container = account_config["source"]["container"]
    storage_key = dbutils.secrets.get(scope="storage_secret", key="storage_key")
    directory = silver_config["destination"]["path"]

    spark.conf.set(
        f"fs.azure.account.key.{account}.dfs.core.windows.net",
        storage_key
    )

    path = f"abfss://{container}@{account}.dfs.core.windows.net/bronze/{year}/{month:02d}/{day:02d}"

    parse_actions = silver_config["action"]["parse_type"]
    
    df_bronze = spark.read.json(path)
    df_bronze.cache()
    df_bronze.count()  # trigger cache

    for action_type in parse_actions:
        parse_func = ParseRegistry.get_parse(action_type)
        df_parsed = parse_func(spark, df_bronze)
        df_parsed.write.mode("overwrite").parquet(f"abfss://{container}@{account}.dfs.core.windows.net/{directory}/{action_type}/{year}/{month:02d}/{day:02d}")

    df_bronze.unpersist()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day",   type=int)
    args = parser.parse_args()

    silver_layer_execution(args.year, args.month, args.day)