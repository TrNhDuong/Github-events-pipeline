from pyspark.sql import DataFrame, SparkSession
from src.core.base_transformation import BaseTransform
from src.core.registry import TransformRegistry

@TransformRegistry.register("push_transform")
class PushTransform(BaseTransform):
    def transform(self, df: DataFrame, spark: SparkSession) -> DataFrame:
        standardized_df = (
            df.withColumn("hour_of_day", hour(col("created_at")))
            .withColumn("date", to_date(col("created_at")))
            .withColumn("year", year(col("created_at")))
            .withColumn("month", month(col("created_at")))
        )
        gold_df = (
            standardized_df
            .groupBy("hour_of_day", "date", "year", "month")
            .agg(count("event_id").alias("event_count"))
            .orderBy("hour_of_day")
        )
        return gold_df