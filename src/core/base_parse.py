from spark.sql import DataFrame, SparkSession

class BaseParse():
    def __init__(self):
        pass

    @abstractmethod
    def parse(self, df: DataFrame, spark: SparkSession) -> DataFrame:
        pass
