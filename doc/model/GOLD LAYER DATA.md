# Gold Layer — Star Schema Design
> **Source:** GitHub Archive Events · **Silver → Gold transformation**  
> **Grain:** 1 row = 1 event · **Format:** Delta / Parquet

---

## Table of Contents

- [Overview](#overview)
- [Shared Dimensions](#shared-dimensions)
- [Fact Tables](#fact-tables)
  - [① Fact\_DevActivity](#-fact_devactivity)
  - [② Fact\_Community](#-fact_community)
  - [③ Fact\_IssueLifecycle](#-fact_issuelifecycle)
- [Analytics Queries](#analytics-queries)
  - [Development Activity](#development-activity)
  - [Community Engagement](#community-engagement)
  - [Issue Lifecycle](#issue-lifecycle)
  - [Cross-Domain](#cross-domain)
- [Design Notes](#design-notes)

---

## Overview

Silver layer lưu toàn bộ 8 event types trong **một bảng sparse matrix** (nhiều cột NULL).  
Gold layer tách thành **3 Fact tables** theo domain phân tích, dùng chung **4 Shared Dimensions**.

```
Silver (1 bảng, sparse)
        │
        ├─── filter event_type ──► Fact_DevActivity     (push, PR, create, delete)
        ├─── filter event_type ──► Fact_Community        (star, fork, comment)
        └─── filter event_type ──► Fact_IssueLifecycle   (issue, comment)
                                         │
                              Dim_Date · Dim_Actor · Dim_Repo · Dim_Org
```

---

## Shared Dimensions

Bốn dimension dùng chung cho tất cả Fact tables. Mỗi Fact chứa FK trỏ về đây.

### `Dim_Date`

| Column | Type | Description |
| :--- | :--- | :--- |
| `date_id` 🔑 | `INT` | Surrogate key (format `YYYYMMDD`) |
| `date_actual` | `DATE` | Ngày thực tế |
| `year` | `INT` | Năm |
| `month` | `INT` | Tháng (1–12) |
| `day` | `INT` | Ngày trong tháng |
| `quarter` | `INT` | Quý (1–4) |
| `week_of_year` | `INT` | Tuần trong năm |
| `weekday_name` | `STRING` | Tên ngày (Monday, …) |
| `is_weekend` | `BOOLEAN` | Có phải cuối tuần không |

> **Nguồn:** Derived từ `created_at` của Silver layer.

---

### `Dim_Actor`

| Column | Type | Description |
| :--- | :--- | :--- |
| `actor_id` 🔑 | `BIGINT` | ID gốc từ GitHub |
| `actor_login` | `STRING` | Username (handle) |
| `actor_type` | `STRING` | `"User"` hoặc `"Bot"` |
| `first_seen_at` | `TIMESTAMP` | Lần đầu xuất hiện trong dataset |

> **Nguồn:** `actor.id`, `actor.login` từ Silver common attributes.

---

### `Dim_Repo`

| Column | Type | Description |
| :--- | :--- | :--- |
| `repo_id` 🔑 | `BIGINT` | ID gốc từ GitHub |
| `repo_name` | `STRING` | Full name (`owner/repo`) |
| `org_id` | `BIGINT` | FK → `Dim_Org` (nullable) |
| `primary_language` | `STRING` | Ngôn ngữ chính (enriched) |

> **Nguồn:** `repo.id`, `repo.name` từ Silver. `primary_language` cần enrich từ GitHub API.

---

### `Dim_Org` *(optional)*

| Column | Type | Description |
| :--- | :--- | :--- |
| `org_id` 🔑 | `BIGINT` | ID gốc từ GitHub |
| `org_name` | `STRING` | Tên organization |
| `org_type` | `STRING` | `"Organization"` hoặc `"User"` |

> **Nguồn:** `org.id` từ Silver (nullable — không phải event nào cũng có org).

---

## Fact Tables

### ① `Fact_DevActivity`

> **Mục tiêu:** Đo lường hoạt động phát triển thực sự — commit, PR, quản lý branch/tag.

**Event types:** `PushEvent` · `PullRequestEvent` · `CreateEvent` · `DeleteEvent`

```sql
-- Silver → Fact_DevActivity
SELECT * FROM silver
WHERE event_type IN ('PushEvent', 'PullRequestEvent', 'CreateEvent', 'DeleteEvent')
```

| Column | Type | Source (Silver) | Description |
| :--- | :--- | :--- | :--- |
| `event_id` 🔑 | `STRING` | `event_id` | Primary key |
| `date_id` 📎 | `INT` | derived from `created_at` | FK → `Dim_Date` |
| `actor_id` 📎 | `BIGINT` | `actor_id` | FK → `Dim_Actor` |
| `repo_id` 📎 | `BIGINT` | `repo_id` | FK → `Dim_Repo` |
| `event_type` | `STRING` | `event_type` | Degenerate dim — loại event |
| `push_commit_count` | `INT` | `push_commit_count` | **Measure** — số commit trong push |
| `push_ref` | `STRING` | `push_ref` | Branch/tag được push tới |
| `pr_action` | `STRING` | `pr_action` | `opened` / `closed` / `reopened` |
| `pr_number` | `INT` | `pr_number` | Số PR trên GitHub |
| `pr_id` | `BIGINT` | `pr_id` | ID kỹ thuật của PR |
| `pr_is_merged` | `BOOLEAN` | `pr_is_merged` | PR có được merge không |
| `create_ref_type` | `STRING` | `create_ref_type` | `repository` / `branch` / `tag` |
| `create_ref_name` | `STRING` | `create_ref_name` | Tên branch/tag được tạo |
| `delete_ref_type` | `STRING` | `delete_ref_type` | `branch` / `tag` |
| `delete_ref_name` | `STRING` | `delete_ref_name` | Tên branch/tag bị xóa |
| `created_at` | `TIMESTAMP` | `created_at` | Timestamp gốc |

> **Lưu ý sparse:** Mỗi row chỉ có 1 `event_type` — các cột còn lại sẽ `NULL`. Parquet/Delta tối ưu tốt cho pattern này.

---

### ② `Fact_Community`

> **Mục tiêu:** Đo lường mức độ quan tâm từ cộng đồng — star, fork, thảo luận.

**Event types:** `WatchEvent` · `ForkEvent` · `IssueCommentEvent`

```sql
-- Silver → Fact_Community
SELECT * FROM silver
WHERE event_type IN ('WatchEvent', 'ForkEvent', 'IssueCommentEvent')
```

| Column | Type | Source (Silver) | Description |
| :--- | :--- | :--- | :--- |
| `event_id` 🔑 | `STRING` | `event_id` | Primary key |
| `date_id` 📎 | `INT` | derived | FK → `Dim_Date` |
| `actor_id` 📎 | `BIGINT` | `actor_id` | FK → `Dim_Actor` |
| `repo_id` 📎 | `BIGINT` | `repo_id` | FK → `Dim_Repo` |
| `org_id` 📎 | `BIGINT` | `org_id` | FK → `Dim_Org` (nullable) |
| `event_type` | `STRING` | `event_type` | Degenerate dim |
| `watch_action` | `STRING` | `watch_action` | Thường là `"started"` |
| `fork_new_repo_id` | `BIGINT` | `fork_new_repo_id` | ID của repo fork mới tạo |
| `fork_new_repo_name` | `STRING` | `fork_new_repo_name` | Tên repo fork mới tạo |
| `comment_id` | `BIGINT` | `comment_id` | ID của comment |
| `comment_action` | `STRING` | `comment_action` | `created` / `edited` / `deleted` |
| `comment_target_issue_id` | `BIGINT` | `comment_target_issue_id` | Issue/PR được comment vào |
| `created_at` | `TIMESTAMP` | `created_at` | Timestamp gốc |

---

### ③ `Fact_IssueLifecycle`

> **Mục tiêu:** Theo dõi vòng đời của issue — từ lúc mở đến lúc đóng, và thảo luận xung quanh.

**Event types:** `IssuesEvent` · `IssueCommentEvent`

```sql
-- Silver → Fact_IssueLifecycle
SELECT * FROM silver
WHERE event_type IN ('IssuesEvent', 'IssueCommentEvent')
```

| Column | Type | Source (Silver) | Description |
| :--- | :--- | :--- | :--- |
| `event_id` 🔑 | `STRING` | `event_id` | Primary key |
| `date_id` 📎 | `INT` | derived | FK → `Dim_Date` |
| `actor_id` 📎 | `BIGINT` | `actor_id` | FK → `Dim_Actor` |
| `repo_id` 📎 | `BIGINT` | `repo_id` | FK → `Dim_Repo` |
| `event_type` | `STRING` | `event_type` | Degenerate dim |
| `issue_id` | `BIGINT` | `issue_id` | ID kỹ thuật của issue |
| `issue_number` | `INT` | `issue_number` | Số issue trên GitHub |
| `issue_action` | `STRING` | `issue_action` | `opened` / `closed` / `reopened` |
| `comment_id` | `BIGINT` | `comment_id` | ID comment (nếu là CommentEvent) |
| `comment_action` | `STRING` | `comment_action` | `created` / `edited` / `deleted` |
| `comment_target_issue_id` | `BIGINT` | `comment_target_issue_id` | Issue cha của comment |
| `created_at` | `TIMESTAMP` | `created_at` | Timestamp gốc |

> **Overlap có chủ ý:** `IssueCommentEvent` xuất hiện ở cả `Fact_Community` lẫn `Fact_IssueLifecycle`.  
> — Community hỏi: *"Repo này sôi nổi không?"*  
> — IssueLifecycle hỏi: *"Issue này được thảo luận đến đâu?"*  
> Hai góc nhìn khác nhau → giữ ở hai Fact là đúng.

---

## Analytics Queries

### Development Activity

**① Repo nào có nhiều commit nhất theo tháng?**

```sql
SELECT
  r.repo_name,
  d.year,
  d.month,
  SUM(f.push_commit_count) AS total_commits
FROM Fact_DevActivity f
JOIN Dim_Repo r  ON f.repo_id  = r.repo_id
JOIN Dim_Date d  ON f.date_id  = d.date_id
WHERE f.event_type = 'PushEvent'
GROUP BY r.repo_name, d.year, d.month
ORDER BY total_commits DESC
```

---

**② Tỷ lệ PR được merge so với tổng PR closed?**

```sql
SELECT
  r.repo_name,
  COUNT(*)                                                              AS total_closed,
  SUM(CASE WHEN f.pr_is_merged THEN 1 ELSE 0 END)                     AS merged,
  ROUND(100.0 * SUM(CASE WHEN f.pr_is_merged THEN 1 ELSE 0 END)
    / COUNT(*), 1)                                                      AS merge_rate_pct
FROM Fact_DevActivity f
JOIN Dim_Repo r ON f.repo_id = r.repo_id
WHERE f.event_type = 'PullRequestEvent'
  AND f.pr_action  = 'closed'
GROUP BY r.repo_name
ORDER BY merge_rate_pct DESC
```

---

**③ Top 10 developer push nhiều commit nhất trong 30 ngày qua?**

```sql
SELECT
  a.actor_login,
  COUNT(*)                   AS push_events,
  SUM(f.push_commit_count)   AS total_commits
FROM Fact_DevActivity f
JOIN Dim_Actor a ON f.actor_id  = a.actor_id
JOIN Dim_Date  d ON f.date_id   = d.date_id
WHERE f.event_type    = 'PushEvent'
  AND d.date_actual  >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY a.actor_login
ORDER BY total_commits DESC
LIMIT 10
```

---

**④ Branch được tạo nhưng chưa bị xóa (đang sống)?**

```sql
SELECT created.repo_id, created.create_ref_name AS branch_name
FROM Fact_DevActivity created
WHERE created.event_type    = 'CreateEvent'
  AND created.create_ref_type = 'branch'
  AND NOT EXISTS (
    SELECT 1
    FROM Fact_DevActivity deleted
    WHERE deleted.event_type     = 'DeleteEvent'
      AND deleted.delete_ref_name = created.create_ref_name
      AND deleted.repo_id          = created.repo_id
  )
```

---

### Community Engagement

**⑤ Repo nào tăng star nhanh nhất theo tuần?**

```sql
SELECT
  r.repo_name,
  d.year,
  d.week_of_year,
  COUNT(*) AS new_stars
FROM Fact_Community f
JOIN Dim_Repo r ON f.repo_id = r.repo_id
JOIN Dim_Date d ON f.date_id = d.date_id
WHERE f.event_type = 'WatchEvent'
GROUP BY r.repo_name, d.year, d.week_of_year
ORDER BY new_stars DESC
```

---

**⑥ Ai fork repo nào, khi nào?**

```sql
SELECT
  r.repo_name                     AS source_repo,
  a.actor_login                   AS forked_by,
  f.fork_new_repo_name            AS new_fork_repo,
  d.date_actual                   AS forked_at
FROM Fact_Community f
JOIN Dim_Repo  r ON f.repo_id  = r.repo_id
JOIN Dim_Actor a ON f.actor_id = a.actor_id
JOIN Dim_Date  d ON f.date_id  = d.date_id
WHERE f.event_type = 'ForkEvent'
ORDER BY d.date_actual DESC
```

---

**⑦ Engagement score tổng hợp (star + fork + comment) theo repo?**

```sql
SELECT
  r.repo_name,
  SUM(CASE WHEN f.event_type = 'WatchEvent'        THEN 3 ELSE 0 END)
+ SUM(CASE WHEN f.event_type = 'ForkEvent'          THEN 5 ELSE 0 END)
+ SUM(CASE WHEN f.event_type = 'IssueCommentEvent'  THEN 1 ELSE 0 END)
    AS engagement_score
FROM Fact_Community f
JOIN Dim_Repo r ON f.repo_id = r.repo_id
GROUP BY r.repo_name
ORDER BY engagement_score DESC
```

> **Trọng số đề xuất:** Star = 3 · Fork = 5 · Comment = 1. Điều chỉnh tuỳ mục đích phân tích.

---

**⑧ Org nào có cộng đồng hoạt động nhất?**

```sql
SELECT
  o.org_name,
  COUNT(DISTINCT f.actor_id)  AS unique_actors,
  COUNT(*)                    AS total_events
FROM Fact_Community f
JOIN Dim_Org o ON f.org_id = o.org_id
WHERE f.event_type IN ('WatchEvent', 'ForkEvent')
GROUP BY o.org_name
ORDER BY unique_actors DESC
```

---

### Issue Lifecycle

**⑨ Thời gian trung bình từ mở đến đóng issue theo repo?**

```sql
SELECT
  r.repo_name,
  AVG(DATEDIFF('day', opened.created_at, closed.created_at)) AS avg_days_to_close
FROM Fact_IssueLifecycle opened
JOIN Fact_IssueLifecycle closed
  ON  opened.issue_id    = closed.issue_id
  AND closed.issue_action = 'closed'
JOIN Dim_Repo r ON opened.repo_id = r.repo_id
WHERE opened.issue_action = 'opened'
GROUP BY r.repo_name
ORDER BY avg_days_to_close DESC
```

---

**⑩ Số issue đang mở (chưa close) theo repo — backlog?**

```sql
SELECT
  r.repo_name,
  COUNT(DISTINCT opened.issue_id) AS open_issues
FROM Fact_IssueLifecycle opened
JOIN Dim_Repo r ON opened.repo_id = r.repo_id
WHERE opened.issue_action = 'opened'
  AND NOT EXISTS (
    SELECT 1
    FROM Fact_IssueLifecycle closed
    WHERE closed.issue_id     = opened.issue_id
      AND closed.issue_action  = 'closed'
  )
GROUP BY r.repo_name
ORDER BY open_issues DESC
```

---

**⑪ Issue nào được thảo luận nhiều nhất (hot issues)?**

```sql
SELECT
  f.comment_target_issue_id  AS issue_id,
  r.repo_name,
  COUNT(*)                   AS comment_count
FROM Fact_IssueLifecycle f
JOIN Dim_Repo r ON f.repo_id = r.repo_id
WHERE f.event_type = 'IssueCommentEvent'
GROUP BY f.comment_target_issue_id, r.repo_name
ORDER BY comment_count DESC
LIMIT 20
```

---

**⑫ Tỷ lệ reopen issue — dấu hiệu fix chưa triệt để?**

```sql
SELECT
  r.repo_name,
  COUNT(DISTINCT issue_id) AS reopened_issues
FROM Fact_IssueLifecycle f
JOIN Dim_Repo r ON f.repo_id = r.repo_id
WHERE f.issue_action = 'reopened'
GROUP BY r.repo_name
ORDER BY reopened_issues DESC
```

---

### Cross-Domain

**⑬ Repo health — vừa code nhiều, vừa được cộng đồng quan tâm?**

```sql
SELECT
  r.repo_name,
  dev.total_commits,
  comm.total_stars,
  comm.total_forks
FROM Dim_Repo r
JOIN (
  SELECT repo_id, SUM(push_commit_count) AS total_commits
  FROM Fact_DevActivity
  WHERE event_type = 'PushEvent'
  GROUP BY repo_id
) dev  ON r.repo_id = dev.repo_id
JOIN (
  SELECT
    repo_id,
    SUM(CASE WHEN event_type = 'WatchEvent' THEN 1 ELSE 0 END) AS total_stars,
    SUM(CASE WHEN event_type = 'ForkEvent'  THEN 1 ELSE 0 END) AS total_forks
  FROM Fact_Community
  GROUP BY repo_id
) comm ON r.repo_id = comm.repo_id
ORDER BY total_commits DESC
```

---

**⑭ Developer profile toàn diện — push, PR, comment?**

```sql
SELECT
  a.actor_login,
  SUM(d.push_commit_count)                                           AS total_commits,
  COUNT(DISTINCT CASE WHEN d.event_type = 'PullRequestEvent'
    THEN d.event_id END)                                             AS total_prs,
  COUNT(DISTINCT CASE WHEN i.event_type = 'IssueCommentEvent'
    THEN i.event_id END)                                             AS total_comments
FROM Dim_Actor a
LEFT JOIN Fact_DevActivity    d ON a.actor_id = d.actor_id
LEFT JOIN Fact_IssueLifecycle i ON a.actor_id = i.actor_id
WHERE a.actor_login = :target_login
GROUP BY a.actor_login
```

---

## Design Notes

### Event overlap là intentional

`IssueCommentEvent` xuất hiện ở **hai** Fact tables:

| Fact | Câu hỏi được trả lời |
| :--- | :--- |
| `Fact_Community` | Repo này có cộng đồng sôi nổi không? (đếm interaction) |
| `Fact_IssueLifecycle` | Issue này được thảo luận đến đâu? (link về issue cụ thể) |

Đây không phải lỗi thiết kế — đây là **hai business view khác nhau** trên cùng một sự kiện.

---

### Degenerate dimensions

Các cột như `event_type`, `pr_action`, `issue_action` có cardinality thấp (vài giá trị cố định) và được giữ **thẳng trong Fact**, không tách ra bảng riêng. Đây là pattern chuẩn trong Star Schema.

---

### Khi nào nên thêm Aggregated Mart?

Nếu dataset lớn (hàng tỷ events), các query dạng self-join (time-to-close, branch alive) sẽ nặng.  
Cân nhắc thêm một lớp **Mart** được pre-compute:

| Mart | Nội dung |
| :--- | :--- |
| `Mart_IssueResolution` | `issue_id`, `opened_at`, `closed_at`, `days_to_close` |
| `Mart_RepoDailyStats` | Tổng commit/star/fork theo `repo_id` + `date_id` |
| `Mart_DeveloperActivity` | Commit/PR/comment tổng hợp theo `actor_id` + tháng |

---

*Generated from GitHub Archive Silver layer — 8 event types: PushEvent, PullRequestEvent, IssuesEvent, IssueCommentEvent, WatchEvent, ForkEvent, CreateEvent, DeleteEvent.*