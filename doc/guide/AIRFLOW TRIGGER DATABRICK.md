# Airflow Trigger Databricks Notebook & Local Trigger Guide

---

## 1. Cài đặt provider Databricks cho Airflow

```bash
pip install apache-airflow-providers-databricks
```

---

## 2. Setup Airflow Connection tới Databricks

```
Airflow UI
    → Admin
    → Connections
    → Add Connection

Connection Id  : databricks_default
Connection Type: Databricks
Host           : https://adb-xxxxx.azuredatabricks.net
Password       : your-databricks-token
```

**Lấy token ở đâu:**
```
Databricks UI
    → Click avatar (góc trên phải)
    → User Settings
    → Access Tokens
    → Generate New Token
    → Copy token
```

---

## 3. Lấy Cluster ID

```
Databricks UI
    → Compute
    → Chọn cluster
    → Tags
    → Copy "ClusterId"
```

Hoặc qua CLI:
```bash
databricks clusters list
# Output:
# CLUSTER_ID        NAME
# 1234-567890-abc   my-cluster
```

---

## 4. Airflow DAG — Trigger Notebook

### 4.1 — DAG cơ bản (1 notebook)

```python
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

with DAG(
    dag_id='github_archive_pipeline',
    schedule_interval='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=True,
    tags=['databricks', 'github_archive']
) as dag:

    bronze = DatabricksSubmitRunOperator(
        task_id='bronze',
        databricks_conn_id='databricks_default',
        existing_cluster_id='your-cluster-id',
        notebook_task={
            'notebook_path': '/Repos/your-repo/notebooks/bronze',
            'base_parameters': {
                'year':  '{{ execution_date.year }}',
                'month': '{{ execution_date.month }}',
                'day':   '{{ execution_date.day }}',
                'hour':  '{{ execution_date.hour }}',
            }
        }
    )
```

### 4.2 — DAG đầy đủ Bronze → Silver → Gold

```python
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import logging

# ── Config ────────────────────────────────────────────────────
CLUSTER_ID   = "your-cluster-id"
CONN_ID      = "databricks_default"
NOTEBOOK_DIR = "/Repos/your-repo/notebooks"

default_args = {
    'owner':            'data-engineer',
    'retries':          2,
    'retry_delay':      300,  # 5 phút
    'email_on_failure': False,
}

# ── DAG ───────────────────────────────────────────────────────
with DAG(
    dag_id='github_archive_pipeline',
    default_args=default_args,
    schedule_interval='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=True,
    max_active_runs=3,      # cho phép 3 run song song (backfill)
    tags=['databricks', 'github_archive']
) as dag:

    # ── Params dùng chung ─────────────────────────────────────
    params = {
        'year':  '{{ execution_date.year }}',
        'month': '{{ execution_date.month }}',
        'day':   '{{ execution_date.day }}',
        'hour':  '{{ execution_date.hour }}',
    }

    def log_start(**context):
        logging.info(
            f"Starting pipeline for "
            f"{context['execution_date']}"
        )

    start = PythonOperator(
        task_id='start',
        python_callable=log_start,
    )

    # ── Bronze ────────────────────────────────────────────────
    bronze = DatabricksSubmitRunOperator(
        task_id='bronze',
        databricks_conn_id=CONN_ID,
        existing_cluster_id=CLUSTER_ID,
        notebook_task={
            'notebook_path': f'{NOTEBOOK_DIR}/bronze',
            'base_parameters': params
        },
        polling_period_seconds=30,  # check status mỗi 30s
    )

    # ── Silver ────────────────────────────────────────────────
    silver = DatabricksSubmitRunOperator(
        task_id='silver',
        databricks_conn_id=CONN_ID,
        existing_cluster_id=CLUSTER_ID,
        notebook_task={
            'notebook_path': f'{NOTEBOOK_DIR}/silver',
            'base_parameters': params
        },
        polling_period_seconds=30,
    )

    # ── Gold ──────────────────────────────────────────────────
    gold = DatabricksSubmitRunOperator(
        task_id='gold',
        databricks_conn_id=CONN_ID,
        existing_cluster_id=CLUSTER_ID,
        notebook_task={
            'notebook_path': f'{NOTEBOOK_DIR}/gold',
            'base_parameters': params
        },
        polling_period_seconds=30,
    )

    def log_done(**context):
        logging.info(
            f"Pipeline done for "
            f"{context['execution_date']}"
        )

    done = PythonOperator(
        task_id='done',
        python_callable=log_done,
    )

    # ── Thứ tự chạy ───────────────────────────────────────────
    start >> bronze >> silver >> gold >> done
```

---

## 5. Trigger từ Airflow UI

```
Airflow UI (http://localhost:8080)
    → Tìm DAG: github_archive_pipeline
    → Bấm ▶ Trigger DAG
    → Conf (JSON) — truyền params tay:
```

```json
{
    "year":  "2024",
    "month": "03",
    "day":   "01",
    "hour":  "5"
}
```

---

## 6. Trigger từ Airflow CLI

```bash
# Trigger toàn bộ DAG
airflow dags trigger github_archive_pipeline \
    --conf '{"year":"2024","month":"03","day":"01","hour":"5"}'

# Test 1 task cụ thể (không cần chạy cả DAG)
airflow tasks test github_archive_pipeline bronze 2024-03-01

# Test Silver
airflow tasks test github_archive_pipeline silver 2024-03-01

# Backfill từ ngày đến ngày
airflow dags backfill github_archive_pipeline \
    --start-date 2024-03-01 \
    --end-date 2024-03-31
```

---

## 7. Trigger từ Airflow REST API

```bash
curl -X POST \
  http://localhost:8080/api/v1/dags/github_archive_pipeline/dagRuns \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{
    "conf": {
        "year":  "2024",
        "month": "03",
        "day":   "01",
        "hour":  "5"
    }
  }'
```

---

## 8. Trigger Databricks Notebook từ Local (không qua Airflow)

### 8.1 — Databricks CLI

```bash
# Cài CLI
pip install databricks-cli

# Config (1 lần)
databricks configure --token

# Trigger 1 notebook
databricks runs submit \
    --existing-cluster-id your-cluster-id \
    --notebook-task '{
        "notebook_path": "/Repos/your-repo/notebooks/bronze",
        "base_parameters": {
            "year":  "2024",
            "month": "03",
            "day":   "01",
            "hour":  "5"
        }
    }'

# Xem kết quả run
databricks runs get --run-id <run_id>
```

### 8.2 — Python Script (Databricks SDK)

```python
# run_pipeline.py
# Cài: pip install databricks-sdk

import os
import sys
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import NotebookTask

# ── Config ────────────────────────────────────────────────────
w = WorkspaceClient(
    host  = os.environ["DATABRICKS_HOST"],
    token = os.environ["DATABRICKS_TOKEN"]
)

CLUSTER_ID   = os.environ["DATABRICKS_CLUSTER_ID"]
NOTEBOOK_DIR = "/Repos/your-repo/notebooks"

# ── Nhận params từ command line ───────────────────────────────
# Usage: python run_pipeline.py 2024 03 01 5
year  = sys.argv[1]
month = sys.argv[2]
day   = sys.argv[3]
hour  = sys.argv[4]

params = {
    "year":  year,
    "month": month,
    "day":   day,
    "hour":  hour,
}

print(f"Running pipeline for {year}-{month}-{day} hour {hour}")

# ── Chạy tuần tự Bronze → Silver → Gold ──────────────────────
notebooks = ["bronze", "silver", "gold"]

for name in notebooks:
    print(f"\n▶ Running {name}...")

    run = w.jobs.submit(
        run_name=f"manual-{name}-{year}{month}{day}{hour}",
        existing_cluster_id=CLUSTER_ID,
        notebook_task=NotebookTask(
            notebook_path=f"{NOTEBOOK_DIR}/{name}",
            base_parameters=params
        )
    )

    # Chờ notebook chạy xong mới chạy tiếp
    result = w.jobs.wait_get_run_job_terminated(run.run_id)

    state = result.state.result_state.value
    if state != "SUCCESS":
        print(f"❌ {name} FAILED — state: {state}")
        print(f"   Log: {result.run_page_url}")
        sys.exit(1)

    print(f"✅ {name} done")

print(f"\n🎉 Pipeline complete!")
```

**Chạy từ terminal:**
```bash
# Set env variables
export DATABRICKS_HOST="https://adb-xxxxx.azuredatabricks.net"
export DATABRICKS_TOKEN="your-token"
export DATABRICKS_CLUSTER_ID="your-cluster-id"

# Trigger pipeline
python run_pipeline.py 2024 03 01 5
```

### 8.3 — Script với .env file (tiện hơn)

```bash
# Cài python-dotenv
pip install python-dotenv
```

```bash
# Tạo file .env (không commit lên GitHub)
# .env
DATABRICKS_HOST=https://adb-xxxxx.azuredatabricks.net
DATABRICKS_TOKEN=your-token
DATABRICKS_CLUSTER_ID=your-cluster-id
```

```python
# Thêm vào đầu run_pipeline.py
from dotenv import load_dotenv
load_dotenv()  # tự đọc .env file

# Phần còn lại giữ nguyên
w = WorkspaceClient(
    host  = os.environ["DATABRICKS_HOST"],
    token = os.environ["DATABRICKS_TOKEN"]
)
```

```bash
# .gitignore — không commit .env
.env
```

---

## 9. So sánh các cách trigger

| Cách | Khi nào dùng |
|---|---|
| Airflow UI | Demo, trigger thủ công 1 lần |
| Airflow CLI `tasks test` | Debug 1 task cụ thể |
| Airflow CLI `dags backfill` | Backfill data nhiều ngày |
| Databricks CLI | Test nhanh 1 notebook |
| Python SDK script | Dev local, test end-to-end |
| Airflow DAG schedule | Production, chạy tự động |

---

## 10. Troubleshooting

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `Connection not found` | Chưa setup Airflow Connection | Vào Admin → Connections thêm lại |
| `Cluster not found` | Sai cluster ID | Check lại `databricks clusters list` |
| `Notebook not found` | Sai notebook path | Check path trong Databricks UI → Repos |
| `Widget not found` | Notebook chạy tay không có widget | Thêm `dbutils.widgets.text("year", "2024")` vào đầu notebook |
| `Token expired` | Token hết hạn | Generate token mới trong Databricks UI |
| `Run failed` | Lỗi trong notebook | Vào Databricks UI → Runs → xem log chi tiết |