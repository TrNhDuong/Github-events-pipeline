# 1. Base Image: Dùng bản chính thức, ổn định (bỏ đuôi slim đi để tránh lỗi thiếu OS lib)
FROM apache/airflow:2.10.3-python3.12

# 2. [Optional] Switch sang ROOT để cài các gói hệ thống (OS Level)
# Bước này cực quan trọng nếu thư viện Python của bạn cần biên dịch (như psycopg2, pandas, numpy...)
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
         libpq-dev \
         git \
         vim \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 3. Switch lại về user AIRFLOW để cài đặt thư viện Python (Best Practice)
USER airflow

# 4. Copy file requirements vào trong image
COPY requirements.txt /requirements.txt

# 5. Cài đặt các thư viện từ requirements.txt
# --no-cache-dir: Giúp image nhẹ hơn, không lưu cache bộ cài
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /requirements.txt
