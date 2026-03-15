# Github Archive Data Pipeline

## Giới thiệu (Description)
Dự án này là một đường ống dữ liệu (data pipeline) hoàn chỉnh nhằm thu thập, xử lý và phân tích dữ liệu sự kiện từ [GH Archive](https://www.gharchive.org/). Pipeline thực hiện việc trích xuất dữ liệu hàng giờ, lưu trữ (ingest) vào **Azure Data Lake Storage (ADLS) Gen 2**, làm sạch và biến đổi dữ liệu bằng **Azure Databricks**, và điều phối (orchestration) toàn bộ quy trình bằng **Apache Airflow**.

Toàn bộ hệ thống Airflow được đóng gói bằng **Docker** để đảm bảo tính nhất quán và dễ dàng triển khai.

## Công nghệ sử dụng (Tech Stack)
- **Ngôn ngữ**: Python (`pyspark`, `pandas`, `requests`)
- **Lưu trữ**: Azure Data Lake Storage (ADLS) Gen 2
- **Xử lý dữ liệu**: Azure Databricks
- **Điều phối (Orchestration)**: Apache Airflow (Dockerized)
- **Containerization**: Docker & Docker Compose

## Cấu trúc thư mục (Directory Structure)

```text
Github Data Platform/
├── dag/                        # Chứa các file định nghĩa DAG cho Airflow
│   ├── bronze_dag.py
│   └── silver_gold_dag.py
├── pipeline/                   # Chứa mã nguồn xử lý chạy trên Databricks
│   ├── bronze.py
│   ├── silver.py
│   └── gold.py
├── src/                        # Thư viện dùng chung
│   ├── adls/                   # Quản lý kết nối ADLS
│   ├── ingestion/              # Logic thu thập dữ liệu
│   └── transformation/         # Logic parse/clean dữ liệu
├── Dockerfile                  # Định nghĩa Airflow Image tùy chỉnh
├── docker-compose.yml          # Quản lý các service của Airflow
├── .env                        # Biến môi trường (Credentials)
├── requirements.txt            # Thư viện Python bổ sung
└── README.md
```

## Hướng dẫn sử dụng với Docker

### 1. Chuẩn bị biến môi trường
Tạo file `.env` từ mẫu hoặc sửa trực tiếp:
```bash
# Azure Storage
AZURE_STORAGE_ACCOUNT=your_account
AZURE_STORAGE_KEY=your_key

# Databricks Configuration
DATABRICKS_HOST=https://adb-xxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi-xxx
DATABRICKS_CLUSTER_ID=your-cluster-id
DATABRICKS_CONN_ID=databricks_default
AIRFLOW_UID=50000
```

### 2. Build và khởi chạy hệ thống
Sử dụng Docker Compose để build image và chạy các container:
```bash
# Build và chạy ở background
docker compose up --build -d
```
Lệnh này sẽ:
- Build image Airflow tùy chỉnh (có sẵn các provider cho Databricks và Azure).
- Khởi tạo Database cho Airflow.
- Chạy Webserver, Scheduler, Worker và Triggerer.

### 3. Truy cập Airflow UI
- Địa chỉ: [http://localhost:8081](http://localhost:8081)
- User/Pass mặc định: `airflow` / `airflow`

### 4. Kiểm tra kết nối
Hệ thống đã tự động cấu hình Connection `databricks_default` thông qua biến môi trường trong `docker-compose.yml`. Bạn có thể kiểm tra tại **Admin > Connections**.

## Lưu ý về Databricks
- Đảm bảo bạn đã setup **Secret Scope** trên Databricks để lưu trữ Azure Key (Xem hướng dẫn trong `doc/DATABRICKS SECRET SCOPE SETUP.md`).
- Các file trong thư mục `pipeline/` cần được đồng bộ lên **Databricks Repos** để Airflow có thể gọi chạy.
