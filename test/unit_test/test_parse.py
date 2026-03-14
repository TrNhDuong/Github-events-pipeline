import pytest
from pyspark.sql import SparkSession

from src.transformation.parse import (
    parse_push_event,
    parse_pull_request_event,
    parse_issues_event,
    parse_issue_comment_event,
    parse_watch_event,
    parse_fork_event,
    parse_create_event,
    parse_delete_event,
)

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .appName("testing") \
        .master("local[1]") \
        .getOrCreate()

def _get_base_event(event_type: str, id_val: str):
    return {
        "id": id_val,
        "type": event_type,
        "created_at": "2025-01-01T00:00:00Z",
        "actor": {"id": 1, "login": "testuser"},
        "repo": {"id": 10, "name": "org/repo"},
        "org": {"id": 100}
    }

def test_parse_push_event(spark):
    event = _get_base_event("PushEvent", "1")
    event["payload"] = {
        "push_id": 1234, 
        "size": 2, 
        "ref": "refs/heads/main"
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_push_event(spark, df)
    
    columns = result_df.columns
    assert "push_id" in columns
    assert "push_commit_count" in columns
    assert "push_ref" in columns
    assert "event_id" in columns
    
    row = result_df.collect()[0]
    assert row["push_id"] == 1234
    assert row["push_commit_count"] == 2
    assert row["push_ref"] == "refs/heads/main"
    assert row["event_id"] == "1"

def test_parse_pull_request_event(spark):
    event = _get_base_event("PullRequestEvent", "2")
    event["payload"] = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "id": 999,
            "merged": False
        }
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_pull_request_event(spark, df)
    
    row = result_df.collect()[0]
    assert row["pr_action"] == "opened"
    assert row["pr_number"] == 42
    assert row["pr_id"] == 999
    assert row["pr_is_merged"] is False
    assert row["event_id"] == "2"

def test_parse_issues_event(spark):
    event = _get_base_event("IssuesEvent", "3")
    event["payload"] = {
        "action": "closed",
        "issue": {
            "id": 888,
            "number": 12
        }
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_issues_event(spark, df)
    
    row = result_df.collect()[0]
    assert row["issue_action"] == "closed"
    assert row["issue_id"] == 888
    assert row["issue_number"] == 12

def test_parse_issue_comment_event(spark):
    event = _get_base_event("IssueCommentEvent", "4")
    event["payload"] = {
        "action": "created",
        "issue": {"id": 888},
        "comment": {"id": 777}
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_issue_comment_event(spark, df)
    
    row = result_df.collect()[0]
    assert row["comment_action"] == "created"
    assert row["comment_target_issue_id"] == 888
    assert row["comment_id"] == 777

def test_parse_watch_event(spark):
    event = _get_base_event("WatchEvent", "5")
    event["payload"] = {"action": "started"}
    
    df = spark.createDataFrame([event])
    result_df = parse_watch_event(spark, df)
    row = result_df.collect()[0]
    assert row["watch_action"] == "started"

def test_parse_fork_event(spark):
    event = _get_base_event("ForkEvent", "6")
    event["payload"] = {
        "forkee": {
            "id": 555,
            "full_name": "neworg/repo"
        }
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_fork_event(spark, df)
    row = result_df.collect()[0]
    assert row["fork_new_repo_id"] == 555
    assert row["fork_new_repo_name"] == "neworg/repo"

def test_parse_create_event(spark):
    event = _get_base_event("CreateEvent", "7")
    event["payload"] = {
        "ref_type": "branch",
        "ref": "feature-x"
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_create_event(spark, df)
    row = result_df.collect()[0]
    assert row["create_ref_type"] == "branch"
    assert row["create_ref_name"] == "feature-x"

def test_parse_delete_event(spark):
    event = _get_base_event("DeleteEvent", "8")
    event["payload"] = {
        "ref_type": "tag",
        "ref": "v1.0.0"
    }
    
    df = spark.createDataFrame([event])
    result_df = parse_delete_event(spark, df)
    row = result_df.collect()[0]
    assert row["delete_ref_type"] == "tag"
    assert row["delete_ref_name"] == "v1.0.0"
