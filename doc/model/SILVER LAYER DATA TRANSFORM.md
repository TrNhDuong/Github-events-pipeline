# Silver Layer — Data Transformation

> Tài liệu này mô tả các quy tắc transformation được áp dụng lên dữ liệu Bronze layer để tạo ra Silver layer, tập trung vào phân tích **PushEvent**.

---

## Mục lục

- [① Tổng quan](#-tổng-quan)
- [② Thuộc tính chung](#-thuộc-tính-chung-common-attributes)
- [③ Thuộc tính đặc thù — PushEvent](#-thuộc-tính-đặc-thù--pushevent)
- [④ Lưu ý kỹ thuật](#-lưu-ý-kỹ-thuật)

---

## ① Tổng quan

Từ toàn bộ raw GitHub Archive events, Silver layer lọc và giữ lại sự kiện **`PushEvent`** — đại diện cho hoạt động commit code thực tế lên repository, phản ánh trực tiếp tốc độ và khối lượng phát triển phần mềm.

---

## ② Thuộc tính chung (Common Attributes)

Các thuộc tính dưới đây được trích xuất từ root của JSON event object và áp dụng cho mọi event, bao gồm `PushEvent`.

| JSON Path gốc | Tên thuộc tính mới | Vai trò / Mục đích |
| :--- | :--- | :--- |
| `id` | `event_id` | Định danh duy nhất của event. Dùng làm primary key. |
| `type` | `event_type` | Loại event — luôn là `"PushEvent"` trong context này. |
| `created_at` | `created_at` | Timestamp khi event xảy ra. Dùng cho phân tích time-series và trending. |
| `actor.id` | `actor_id` | ID của user đã thực hiện push. Liên kết với User Dimension. |
| `actor.login` | `actor_login` | Username của user thực hiện push. |
| `repo.id` | `repo_id` | ID của repository được push vào. Liên kết với Repo Dimension. |
| `repo.name` | `repo_name` | Tên đầy đủ của repository (format: `owner/repo_name`). |
| `org.id` | `org_id` | *(Optional)* ID của tổ chức sở hữu repository. |

---

## ③ Thuộc tính đặc thù — PushEvent

Các thuộc tính dưới đây được trích xuất từ nested object `payload` và **chỉ có giá trị** khi `event_type = "PushEvent"`.

| JSON Path gốc | Tên thuộc tính mới | Vai trò / Mục đích |
| :--- | :--- | :--- |
| `payload.push_id` | `push_id` | Định danh duy nhất cho hành động push. |
| `payload.size` | `push_commit_count` | Số lượng commit trong push này. Dùng để đo lường code velocity. |
| `payload.ref` | `push_ref` | Git reference được push đến (ví dụ: `refs/heads/main`). Xác định target branch. |

---

## ④ Lưu ý kỹ thuật

- Dữ liệu được lưu trữ theo định dạng **Parquet / Delta** — tối ưu cho columnar storage.
- Chỉ giữ lại các event có `event_type = "PushEvent"`, các event type khác bị loại bỏ ở bước filtering.
- `push_commit_count` là chỉ số cốt lõi để đánh giá **code volume** và **development velocity** theo thời gian.