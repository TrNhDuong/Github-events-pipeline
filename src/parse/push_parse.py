from pyspark.sql import DataFrame, SparkSession
from src.core.base_parse import BaseParse
from src.core.registry import ParseRegistry
from src.parse.common_attribute import _select_common_attributes

@ParseRegistry.register("push_parse")
class PushParse(BaseParse):
    def parse(self, df: DataFrame, spark: SparkSession) -> DataFrame:
        return df.select(
            *_select_common_attributes(),
            col("payload.push_id").alias("push_id"),
            col("payload.size").alias("push_commit_count"),
            col("payload.ref").alias("push_ref")
        )