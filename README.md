# Github Archive Data Pipeline

## Giới thiệu (Description)
Dự án này là một đường ống dữ liệu (data pipeline) hoàn chỉnh nhằm thu thập, xử lý và phân tích dữ liệu sự kiện từ [GH Archive](https://www.gharchive.org/). Pipeline thực hiện việc trích xuất dữ liệu hàng giờ, lưu trữ (ingest) vào **Azure Data Lake Storage (ADLS) Gen 2**, làm sạch và biến đổi dữ liệu bằng **Azure Databricks**, và điều phối (orchestration) toàn bộ quy trình bằng **Apache Airflow** chạy giả lập ở môi trường local.

## Công nghệ sử dụng (Tech Stack)
- **Ngôn ngữ**: Python (sử dụng các thư viện `requests`, `gzip`, `json`)
- **Lưu trữ**: Azure Data Lake Storage (ADLS) Gen 2
- **Xử lý dữ liệu**: Azure Databricks (Databricks Notebooks)
- **Điều phối (Orchestration)**: Apache Airflow (chạy Local)

## Nguồn dữ liệu (Data Source)
- **URL định dạng**: `https://data.gharchive.org/{date}-{hour}.json.gz`
- **Ví dụ gọi API**: `https://data.gharchive.org/2025-01-01-12.json.gz`
- **Định dạng gốc**: JSONL nén dưới dạng `gzip`
- **Kích thước**: Khoảng 100-200MB cho mỗi file dữ liệu hàng giờ

## Cấu trúc thư mục (Directory Structure)

```text
Github Data Platform/
├── doc/
│   ├── AIRFLOW TRIGGER DATABRICK.md
│   ├── DATABRICK SECRET SCOPE SETUP.md
│   └── SILVER LAYER DATA TRANSFORM.md
├── pipeline/
│   ├── 01_bronze.py
│   ├── 02_silver.py
│   └── 03_gold.py
├── src/
│   ├── __init__.py
│   ├── adls/
│   │   ├── __init__.py
│   │   └── adls.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── ingest.py
│   ├── transformation/
│   │   ├── __init__.py
│   │   └── parse.py
│   └── utils/
├── test/
│   └── unit_test/
├── extract_samples.py
├── main.py
├── README.md
├── requirements.txt
└── sample.jsonl
```

## Kiến trúc và Luồng dữ liệu (Data Flow)
Mô hình hoạt động theo lịch trình chạy mỗi giờ một lần (hourly batch processing):
1. **Thu thập dữ liệu (Extract)**: Lập lịch chạy quá trình tải dữ liệu thông qua Airflow. Mã nguồn từ `main.py` sẽ thực thi gọi xuống server của GH Archive theo đúng Ngày-Giờ.
2. **Giải nén & Trích xuất (Decompress & Parse)**: File `gzip` sẽ được decompress trên bộ nhớ và parse lại từng dòng JSON, sau đó tập hợp và được ghi ra file có định dạng `.jsonl`.
3. **Lưu trữ (Ingestion/Bronze Layer)**: Dữ liệu JSONL vừa tạo ra được đưa thẳng vào container dữ liệu thô (Bronze) trên ADLS Gen 2.
4. **Xử lý & Làm sạch (Transformation/Silver Layer)**: Thông qua Apache Airflow kích hoạt Databricks Notebook ở trên Azure để xử lý, làm sạch và định dạng lại cấu trúc dữ liệu. Kết quả lưu tại phân vùng Silver.
5. **Phân tích (Analytics/Gold Layer)**: Dữ liệu sau khi làm sạch tiếp tục được Databricks xử lý tính toán các KPI, metrics chuyên sâu và ghi lại lên ADLS Gen 2 (phân vùng Gold). Dữ liệu này dùng để phục vụ Dashboard hoặc Data Science.

## Hướng dẫn sử dụng

### 1. Chuẩn bị môi trường Python
Cài đặt thư viện yêu cầu:
```bash
pip install -r requirements.txt
```

### 2. Cấu hình Azure & Databricks
- Tạo **Azure Storage Account (ADLS Gen 2)** với kiến trúc thư mục chuẩn: `bronze`, `silver`, `gold`.
- Truy cập **Azure Databricks**, tiến hành mount ADLS Gen 2 vào workspace.
- Upload các notebook xử lý dữ liệu lên Databricks Workspace.

### 3. Chạy Apache Airflow (Local)
Khởi tạo và chạy webserver cũng như scheduler của Airflow ở terminal:
```bash
airflow webserver --port 8080
airflow scheduler
```
Truy cập vào [http://localhost:8080](http://localhost:8080), bật *(unpause)* DAG của Github Archive Data Pipeline để quy trình chạy tự động theo mỗi giờ.
