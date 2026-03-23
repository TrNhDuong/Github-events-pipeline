from spark.sql import DataFrame, SparkSession

class BaseTransform():
    def __init__(self):
        pass

    @abstractmethod
    def transform(self, df: DataFrame, spark: SparkSession) -> DataFrame:
        pass
