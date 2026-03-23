from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col, date_format, to_date, year, month, dayofmonth, 
    quarter, weekofyear, when, lit, 
    hour, count  # Đã bổ sung import còn thiếu
)

class BaseTransform:
    def __init__(self):
        pass

    @abstractmethod
    def transform(self, df: DataFrame, spark: SparkSession) -> DataFrame:
        pass 



class PushEventTransform(BaseTransform):
    def transform(self, df: DataFrame, spark: SparkSession) -> DataFrame:
        standardized_df = (df
            .withColumn("hour_of_day", hour(col("created_at")))
            .withColumn("date", to_date(col("created_at")))
            .withColumn("year", year(col("created_at")))
            .withColumn("month", month(col("created_at")))
        )

        gold_df = (standardized_df
            .groupBy("hour_of_day", "date", "year", "month")
            .agg(count("event_id").alias("event_count"))
            .orderBy("hour_of_day")
        )
        
        return gold_df


class Creator:
    def __init__(self):
        pass

    @abstractmethod
    def create(self):
        pass

class PushEventCreator(Creator):
    def create(self):
        return PushEventTransform()

# Hoàn thiện hàm orchestrator
def transform_silver_to_gold(df: DataFrame, spark: SparkSession, event_types: list[str]) -> DataFrame:
    list_transformer = []
    for event_type in event_types:
        transformer = BaseTransform.get_transformer(event_type)
        list_transformer.append(transformer)
    
    # 2. Thực thi transform và trả về kết quả
    return transformer.transform(df, spark)