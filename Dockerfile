FROM apache/airflow:3.1.8-python3.12

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

# Copy requirements trước khi switch user
COPY requirements.txt /requirements.txt
RUN chmod 644 /requirements.txt

USER airflow

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r /requirements.txt