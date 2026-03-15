import os
from datetime import datetime, timedelta
from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator

# Cấu hình chung
DATABRICKS_CONN_ID = os.getenv("DATABRICKS_CONN_ID", "databricks_default")
DATABRICKS_CLUSTER_ID = os.getenv("DATABRICKS_CLUSTER_ID", "your-cluster-id")
DATABRICKS_REPO_PATH = "/Workspace/Repos/Github-events-pipeline/pipeline"

default_args = {
    'owner': 'data-engineer',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

@dag(
    dag_id='github_silver_gold_transformation',
    default_args=default_args,
    schedule='30 0 * * *',  # Chạy lúc 00:30 mỗi ngày
    start_date=datetime(2026, 3, 15),
    catchup=True,
    max_active_runs=1,
    tags=['databricks', 'silver', 'gold', 'daily']
)
def github_silver_gold_dag():

    # Common parameters for both tasks
    common_params = [
        '--year',  '{{ execution_date.year }}',
        '--month', '{{ execution_date.month }}',
        '--day',   '{{ execution_date.day }}',
    ]

    silver = DatabricksSubmitRunOperator(
        task_id='silver_transformation',
        databricks_conn_id=DATABRICKS_CONN_ID,
        existing_cluster_id=DATABRICKS_CLUSTER_ID,
        spark_python_task={
            'python_file': f'{DATABRICKS_REPO_PATH}/silver.py',
            'parameters':  common_params,
        },
        polling_period_seconds=30
    )

    gold = DatabricksSubmitRunOperator(
        task_id='gold_transformation',
        databricks_conn_id=DATABRICKS_CONN_ID,
        existing_cluster_id=DATABRICKS_CLUSTER_ID,
        spark_python_task={
            'python_file': f'{DATABRICKS_REPO_PATH}/gold.py',
            'parameters':  common_params,
        },
        polling_period_seconds=30
    )

    silver >> gold

# Instantiate the DAG
dag_instance = github_silver_gold_dag()