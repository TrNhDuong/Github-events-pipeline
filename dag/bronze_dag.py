import os
from datetime import datetime, timedelta
from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator

# Cấu hình chung - Đọc từ environment variables (set trong .env qua docker-compose)
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
    dag_id='github_bronze_extraction',
    default_args=default_args,
    schedule_interval='0 * * * *',  # Chạy mỗi giờ
    start_date=datetime(2026, 3, 15),
    catchup=True,
    max_active_runs=3,
    tags=['databricks', 'bronze', 'hourly']
)
def github_bronze_dag():

    DatabricksSubmitRunOperator(
        task_id='extract_github_to_bronze',
        databricks_conn_id=DATABRICKS_CONN_ID,
        existing_cluster_id=DATABRICKS_CLUSTER_ID,
        spark_python_task={
            'python_file': f'{DATABRICKS_REPO_PATH}/bronze.py',
            'parameters': [
                '--year',  '{{ execution_date.year }}',
                '--month', '{{ execution_date.month }}',
                '--day',   '{{ execution_date.day }}',
                '--hour',  '{{ execution_date.hour }}',
            ],
        },
        polling_period_seconds=30
    )

# Instantiate the DAG
dag_instance = github_bronze_dag()