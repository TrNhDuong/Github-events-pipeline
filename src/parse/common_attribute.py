from pyspark.sql.functions import col
    
def _select_common_attributes():
    return [
        col("id").alias("event_id"),
        col("type").alias("event_type"),
        col("created_at").alias("created_at"),
        col("actor.id").alias("actor_id"),
        col("actor.login").alias("actor_login"),
        col("repo.id").alias("repo_id"),
        col("repo.name").alias("repo_name"),
        col("org.id").alias("org_id")
    ]