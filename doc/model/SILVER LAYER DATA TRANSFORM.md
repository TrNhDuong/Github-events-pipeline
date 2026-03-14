# Silver Layer Data Transformation

This document details the transformation rules applied to the Bronze layer data to create the Silver layer. We filter the raw GitHub Archive events to retain only the 8 core event types that are valuable for analyzing repository activity, community engagement, and development lifecycle.

## Core Event Types Processed
1. `PushEvent`
2. `PullRequestEvent`
3. `IssuesEvent`
4. `IssueCommentEvent`
5. `WatchEvent`
6. `ForkEvent`
7. `CreateEvent`
8. `DeleteEvent`

## Common Attributes (Retained for ALL Events)
These attributes are extracted from the root of the JSON event object and are common to all retained events. They form the core dimensions of the dataset.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `id` | `event_id` | Unique identifier for the event. Used as the primary key. |
| `type` | `event_type` | The type of the event (e.g., "PushEvent"). Used for filtering and aggregations. |
| `created_at` | `created_at` | The timestamp when the event occurred. Used for time-series analysis and trending. |
| `actor.id` | `actor_id` | Unique identifier of the user (actor) who triggered the event. Links to the User Dimension. |
| `actor.login` | `actor_login` | Username (handle) of the user who triggered the event. |
| `repo.id` | `repo_id` | Unique identifier of the repository where the event occurred. Links to the Repo Dimension. |
| `repo.name` | `repo_name` | Full name of the repository (format: `owner/repo_name`). Represents the source repository. |
| `org.id` | `org_id` | (Optional) Unique identifier of the organization owning the repository. |

## Event-Specific Attributes (Extracted from `payload`)

Depending on the `event_type`, specific attributes are extracted from the nested `payload` JSON object. This strategy employs a sparse matrix approach: if a row is a `PushEvent`, its specific columns will be populated, but `PullRequestEvent` columns will be `NULL`. This is highly optimal for columnar formats like Parquet/Delta.

### 1. PushEvent
Captures code commits pushed to a branch or tag. Represents the actual coding effort.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.push_id` | `push_id` | Unique identifier for the push action itself. |
| `payload.size` | `push_commit_count` | The number of distinct commits included in this push. Used to measure code volume/velocity. |
| `payload.ref` | `push_ref` | The Git reference (e.g., `refs/heads/main`) being pushed to. Identifies the target branch. |

### 2. PullRequestEvent
Captures lifecycle events of Pull Requests. Represents structured feature development and code integration.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.action` | `pr_action` | The action performed on the PR (e.g., "opened", "closed", "reopened"). |
| `payload.number` | `pr_number` | The PR number on GitHub (e.g., PR #123). |
| `payload.pull_request.id` | `pr_id` | Unique technical identifier of the Pull Request object. |
| `payload.pull_request.merged` | `pr_is_merged` | Boolean flag indicating if a "closed" PR was successfully merged into the target branch. |

### 3. IssuesEvent
Captures lifecycle events of repository Issues. Represents bug tracking and feature requests.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.action` | `issue_action` | The action performed on the issue (e.g., "opened", "closed", "reopened"). |
| `payload.issue.id` | `issue_id` | Unique technical identifier of the Issue object. |
| `payload.issue.number` | `issue_number` | The Issue number on GitHub (e.g., Issue #456). |

### 4. IssueCommentEvent
Captures comments made on Issues or Pull Requests. Represents community engagement and developer communication.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.action` | `comment_action` | The action performed on the comment (e.g., "created", "edited", "deleted"). |
| `payload.issue.id` | `comment_target_issue_id` | The ID of the parent Issue or PR that this comment belongs to. Used to link discussions to their source. |
| `payload.comment.id` | `comment_id` | Unique technical identifier of the comment itself. |

### 5. WatchEvent
Captures when a user "stars" a repository.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.action` | `watch_action` | Typically "started". Represents the action of starring the parent repository. |

### 6. ForkEvent
Captures when a user forks a repository. Represents deep interest in utilizing or contributing to the codebase.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.forkee.id` | `fork_new_repo_id` | The unique ID of the *newly created* destination repository (the fork in the actor's account). |
| `payload.forkee.full_name` | `fork_new_repo_name` | The full name of the *newly created* destination repository (e.g., `actor/forked-repo`). |

### 7. CreateEvent
Captures the creation of a repository, branch, or tag.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.ref_type` | `create_ref_type` | The type of Git object created: "repository", "branch", or "tag". |
| `payload.ref` | `create_ref_name` | The name of the created branch or tag (is naturally `null` if the `ref_type` is "repository"). |

### 8. DeleteEvent
Captures the deletion of a branch or tag. Represents repository housekeeping.

| Original JSON Path | New Attribute Name | Role / Purpose |
| :--- | :--- | :--- |
| `payload.ref_type` | `delete_ref_type` | The type of Git object deleted: "branch" or "tag". |
| `payload.ref` | `delete_ref_name` | The name of the branch or tag that was deleted. |
