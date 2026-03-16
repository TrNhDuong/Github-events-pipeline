# Hướng dẫn Setup Databricks Secret Scope

## 1. Cài Databricks CLI

```bash
pip install databricks-cli
```

## 2. Cấu hình CLI

```bash
databricks configure --token
```

Nhập thông tin khi được hỏi:
- **Host:** `https://adb-7405619615010274.14.azuredatabricks.net`
- **Token:** `<DATABRICKS_TOKEN>`

## 3. Tạo Secret Scope

> Lưu ý: Workspace dùng bản Free/Standard cần thêm flag `--initial-manage-principal users`

```bash
databricks secrets create-scope --scope storage_secret --initial-manage-principal users
```

## 4. Thêm Secret Key

```bash
databricks secrets put --scope storage_secret --key storage_key --string-value "<AZURE_STORAGE_KEY>"
```

Lấy `AZURE_STORAGE_KEY` tại:
**Azure Portal → Storage Account → Security + networking → Access keys → key1**

## 5. Kiểm tra

```bash
databricks secrets list --scope storage_secret
```

## 6. Sử dụng trong Databricks Notebook / Script

```python
storage_key = dbutils.secrets.get(scope="storage_secret", key="storage_key")
```

---

## Lưu ý

- Secret **không thể đọc lại giá trị** sau khi tạo (chỉ dùng được qua `dbutils.secrets.get`)
- Nếu cần update, chạy lại lệnh `put` với giá trị mới — nó sẽ tự override
- Workspace Premium mới có Secret Management UI; bản thường phải dùng CLI