from pyspark.sql import SparkSession 
from pyspark.sql.functions import col 
from functools import reduce
from pyspark.sql import DataFrame
from src.transformation.parse import (
    parse_push_event, parse_pull_request_event,
    parse_issues_event, parse_issue_comment_event,
    parse_watch_event, parse_fork_event,
    parse_create_event, parse_delete_event
)

TYPE_PARSE_MAP = {
    "PushEvent":         parse_push_event,
    "PullRequestEvent":  parse_pull_request_event,
    "IssuesEvent":       parse_issues_event,
    "IssueCommentEvent": parse_issue_comment_event,
    "WatchEvent":        parse_watch_event,
    "ForkEvent":         parse_fork_event,
    "CreateEvent":       parse_create_event,
    "DeleteEvent":       parse_delete_event,
}

def silver_layer_execution(year: int, month: int, day: int):
    spark = SparkSession.builder.appName("silver_layer_execution").getOrCreate()

    path = f"adls://duongbambo.dfs.core.windows.net/githubarchive/bronze/{year}/{month:02d}/{day:02d}"

    df_bronze = spark.read.json(path)
    df_bronze.cache()
    df_bronze.count()  # trigger cache

    # 1 lần scan nhẹ để biết types nào tồn tại
    existing_types = {
        row["type"]
        for row in df_bronze.select("type").distinct().collect()
    }

    for event_type, parse_func in TYPE_PARSE_MAP.items():
        if event_type not in existing_types:  # ← skip nếu không có data
            continue

        df_filtered = df_bronze.filter(col("type") == event_type)
        df_parsed = parse_func(spark, df_filtered)

        # Ghi ra silver layer
        output_path = f"adls://duongbambo.dfs.core.windows.net/githubarchive/silver/{event_type}/{year}/{month:02d}/{day:02d}"
        df_parsed.write.mode("overwrite").parquet(output_path)  # ← ghi output

    df_bronze.unpersist()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day",   type=int)
    args = parser.parse_args()

    silver_layer_execution(args.year, args.month, args.day)