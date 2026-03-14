from pyspark.sql import SparkSession, DataFrame
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

def parse_push_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.push_id").alias("push_id"),
        col("payload.size").alias("push_commit_count"),
        col("payload.ref").alias("push_ref")
    )

def parse_pull_request_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.action").alias("pr_action"),
        col("payload.number").alias("pr_number"),
        col("payload.pull_request.id").alias("pr_id"),
        col("payload.pull_request.merged").alias("pr_is_merged")
    )

def parse_issues_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.action").alias("issue_action"),
        col("payload.issue.id").alias("issue_id"),
        col("payload.issue.number").alias("issue_number")
    )

def parse_issue_comment_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.action").alias("comment_action"),
        col("payload.issue.id").alias("comment_target_issue_id"),
        col("payload.comment.id").alias("comment_id")
    )

def parse_watch_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.action").alias("watch_action")
    )

def parse_fork_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.forkee.id").alias("fork_new_repo_id"),
        col("payload.forkee.full_name").alias("fork_new_repo_name")
    )

def parse_create_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.ref_type").alias("create_ref_type"),
        col("payload.ref").alias("create_ref_name")
    )

def parse_delete_event(spark: SparkSession, df: DataFrame) -> DataFrame:
    return df.select(
        *_select_common_attributes(),
        col("payload.ref_type").alias("delete_ref_type"),
        col("payload.ref").alias("delete_ref_name")
    )