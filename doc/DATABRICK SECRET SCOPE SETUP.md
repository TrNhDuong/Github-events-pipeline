# Databricks Secret Scope — Setup Guide
## Đọc/Ghi ADLS Gen2 không hardcode key

---

## 1. Lấy Storage Account Key từ Azure Portal

```
Azure Portal
    → Storage Accounts
    → Chọn storage account của bạn
    → Security + networking
    → Access keys
    → Copy "key1" (hoặc key2)
```

> ⚠️ **Không paste key này vào code hay commit lên GitHub**

---

## 2. Cài Databricks CLI

```bash
pip install databricks-cli
```

---

## 3. Authenticate CLI với Databricks

```bash
databricks configure --token
```

CLI sẽ hỏi 2 thứ:

```
Databricks Host: https://adb-xxxxx.azuredatabricks.net
Token: your-databricks-token
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

Kiểm tra kết nối thành công:
```bash
databricks clusters list
# Nếu thấy list cluster → OK
```

---

## 4. Tạo Secret Scope

```bash
databricks secrets create-scope --scope myproject
```

Kiểm tra scope đã tạo:
```bash
databricks secrets list-scopes
# Output:
# Name        Backend
# ----------  -------
# myproject   DATABRICKS
```

---

## 5. Lưu Storage Key vào Secret Scope

```bash
databricks secrets put --scope myproject --key adls-key
```

CLI sẽ mở text editor (vim/nano), paste key vào rồi save:
```
# Trong editor:
your-storage-account-key-xxxxxxxxxxxxxxxx
# Save và thoát
```

**Hoặc dùng flag `--string-value` để không mở editor:**
```bash
databricks secrets put \
    --scope myproject \
    --key adls-key \
    --string-value "your-storage-account-key"
```

Kiểm tra key đã lưu (chỉ thấy tên, không thấy value):
```bash
databricks secrets list --scope myproject
# Output:
# Key       Last Updated
# --------  ------------
# adls-key  1234567890
```

---

## 6. Lưu thêm các secret khác (nếu cần)

```bash
# Storage account name
databricks secrets put \
    --scope myproject \
    --key adls-account-name \
    --string-value "yourstorageaccount"

# Container name
databricks secrets put \
    --scope myproject \
    --key adls-container \
    --string-value "yourcontainer"

# Databricks token (nếu cần dùng trong notebook)
databricks secrets put \
    --scope myproject \
    --key databricks-token \
    --string-value "your-databricks-token"
```

---

## 7. Dùng trong Databricks Notebook

### 7.1 — Config Spark kết nối ADLS

```python
# Đọc key từ Secret Scope
storage_key = dbutils.secrets.get(
    scope="myproject",
    key="adls-key"
)

storage_account = dbutils.secrets.get(
    scope="myproject",
    key="adls-account-name"
)

# Config Spark dùng key này
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
```

### 7.2 — Build path động từ Airflow params

```python
# Nhận params từ Airflow
year  = dbutils.widgets.get("year")
month = dbutils.widgets.get("month")
day   = dbutils.widgets.get("day")
hour  = dbutils.widgets.get("hour")

container     = "raw"
storage_acct  = storage_account  # lấy từ secret ở trên

# Build path
input_path = (
    f"abfss://{container}@{storage_acct}.dfs.core.windows.net"
    f"/github/{year}/{month.zfill(2)}/{day.zfill(2)}/{hour}.json.gz"
)

output_path = (
    f"abfss://bronze@{storage_acct}.dfs.core.windows.net"
    f"/github/year={year}/month={month}/day={day}/hour={hour}/"
)

print(f"Input : {input_path}")
print(f"Output: {output_path}")
```

### 7.3 — Đọc data

```python
df = spark.read.json(input_path)

print(f"Row count: {df.count()}")
df.printSchema()
```

### 7.4 — Xử lý Bronze layer

```python
from pyspark.sql.functions import current_timestamp, lit

df_bronze = df \
    .withColumn("ingested_at", current_timestamp()) \
    .withColumn("source", lit("github_archive")) \
    .withColumn("year",  lit(year)) \
    .withColumn("month", lit(month)) \
    .withColumn("day",   lit(day)) \
    .withColumn("hour",  lit(hour))
```

### 7.5 — Ghi vào ADLS

```python
df_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .save(output_path)

print(f"✅ Written to: {output_path}")
```

---

## 8. Notebook đầy đủ (Bronze)

```python
# ── 1. Config ────────────────────────────────────────────────
storage_key = dbutils.secrets.get(
    scope="myproject",
    key="adls-key"
)
storage_account = dbutils.secrets.get(
    scope="myproject",
    key="adls-account-name"
)

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# ── 2. Nhận params từ Airflow ────────────────────────────────
year  = dbutils.widgets.get("year")
month = dbutils.widgets.get("month")
day   = dbutils.widgets.get("day")
hour  = dbutils.widgets.get("hour")

# ── 3. Build path ────────────────────────────────────────────
input_path = (
    f"abfss://raw@{storage_account}.dfs.core.windows.net"
    f"/github/{year}/{month.zfill(2)}/{day.zfill(2)}/{hour}.json.gz"
)
output_path = (
    f"abfss://bronze@{storage_account}.dfs.core.windows.net"
    f"/github/year={year}/month={month}/day={day}/hour={hour}/"
)

print(f"Processing: {input_path}")

# ── 4. Đọc raw data ──────────────────────────────────────────
df = spark.read.json(input_path)
print(f"Row count: {df.count()}")

# ── 5. Transform Bronze ──────────────────────────────────────
from pyspark.sql.functions import current_timestamp, lit

df_bronze = df \
    .withColumn("ingested_at", current_timestamp()) \
    .withColumn("source", lit("github_archive")) \
    .withColumn("year",  lit(year)) \
    .withColumn("month", lit(month)) \
    .withColumn("day",   lit(day)) \
    .withColumn("hour",  lit(hour))

# ── 6. Ghi Bronze ────────────────────────────────────────────
df_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .save(output_path)

print(f"✅ Done: {output_path}")
```

---

## 9. Chú ý quan trọng

### ❌ Không làm:
```python
# Hardcode key
spark.conf.set("fs.azure.account.key...", "abcxyz123...")

# Print key ra log
print(dbutils.secrets.get(scope="myproject", key="adls-key"))
# → Databricks tự block, in ra "******" thay vì key thật
```

### ✅ Nên làm:
```python
# Luôn đọc từ Secret Scope
storage_key = dbutils.secrets.get(scope="myproject", key="adls-key")

# Config 1 lần ở đầu notebook
# Các cell sau dùng path abfss:// bình thường
```

### .gitignore — không commit secret:
```
# .gitignore
.databricks/
*.env
secrets/
```

---

## 10. Troubleshooting

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `Secret does not exist` | Sai scope hoặc key name | Check lại `databricks secrets list --scope myproject` |
| `AuthorizationPermissionMismatch` | Storage key sai | Lấy lại key từ Azure Portal |
| `Container not found` | Sai container name | Check lại tên container trên ADLS |
| `Widget not found` | Chạy notebook tay, không có widget | Dùng `dbutils.widgets.text("year", "2024")` để set default |

### Set default value khi chạy tay (không qua Airflow):
```python
# Thêm vào đầu notebook để test local
dbutils.widgets.text("year",  "2024")
dbutils.widgets.text("month", "03")
dbutils.widgets.text("day",   "01")
dbutils.widgets.text("hour",  "5")

# Sau đó đọc bình thường
year  = dbutils.widgets.get("year")
month = dbutils.widgets.get("month")
```