# T-022 Agency report

**Phase:** 3 · API · **Status:** analyzed · **Size:** M
**Refs:** R6.1–R6.4, spec: Reporting (Agency report), API endpoints (Agency)
**Depends on:** T-017, T-021

## Goal
The agency sees where every article stands, how fast clients approve, and what went live and what's coming — computed on request, matching the spec's decision not to store report data.

## Analysis

### Flow
1. `GET /report` loads all articles and their events for the site, runs `sync_statuses` (T-021) first (spec: "Runs the status check"), then computes every block from that one snapshot.
2. **Status counts:** tally current `status` across all articles, plus a separate "published this month" count (articles with a `published` event whose `at` falls in the current calendar month, server timezone = UTC).
3. **Approval speed:** for each article, find its *first* `sent_for_review` event and its `approved` event (if any); average `(approved.at - first_sent_for_review.at)` across articles that have both. Articles never approved are excluded, not counted as zero.
4. **Change rounds:** per article, count `changes_requested` events; "articles that needed changes" = count of articles with ≥1 such event; rounds per article = that count, shown per article in the list (not just an aggregate).
5. **Upcoming:** Scheduled articles with `publish_at_utc`, sorted soonest first.
6. **Published:** Published articles with `published_url` and publish date, sorted most recent first.
7. **Needs attention:** Failed articles, plus any article carrying a `sync_warning` from the T-021 pass (Late, Changed in WordPress, Missing in WordPress).

### API
`GET /report`

| Case | Status | Body |
| --- | --- | --- |
| OK | 200 | `ReportOut` (see fields below) |

`ReportOut` fields: `status_counts: dict[Status, int]`, `published_this_month: int`, `avg_approval_seconds: float | null` (null when no article has ever been approved), `change_rounds: [{article_id, title, rounds}]`, `upcoming: [{article_id, title, publish_at_utc}]`, `published: [{article_id, title, published_url, published_at}]`, `needs_attention: [{article_id, title, reason: "failed" | "late" | "changed_in_wordpress" | "missing_in_wordpress", detail}]`, `wordpress_unreachable: bool`.

### Core
- `core/domain/report.py`: pure functions over `list[Article]` + `list[Event]` → each block above. No adapter calls inside `report.py` itself — the use case gathers data first, then hands it to these pure functions, keeping the math unit-testable with plain fixtures and no repository at all.
- `core/use_cases/build_report.py`: orchestrates — load articles/events via the repository, run `sync_status.sync_statuses`, call each `report.py` function, assemble `ReportOut`.

### Edge cases
| Case | Behavior |
| --- | --- |
| No articles yet | All counts zero, lists empty, `avg_approval_seconds: null` |
| An article was sent for review, pulled back, then sent again, then approved | Approval speed uses the *first* `sent_for_review`, per spec wording ("average time from **first** sent for review to approved") |
| WordPress unreachable during the report's own status check | Report still renders from stored data; `wordpress_unreachable: true`, Needs attention still shows anything already known (e.g. stored Failed), just not fresh sync warnings |

## Acceptance criteria
- [ ] Status counts match a hand-built fixture set of articles across all seven statuses.
- [ ] Published-this-month counts only `published` events within the current UTC month.
- [ ] Approval speed averages only articles that reached Approved, using the first send-for-review timestamp.
- [ ] Change rounds count matches the number of `changes_requested` events per article.
- [ ] Needs attention lists Failed articles and every sync-warning case from T-021.
- [ ] Swagger and Postman updated.

## Tasks
- [ ] `core/domain/report.py`: pure calculation functions.
- [ ] `core/use_cases/build_report.py`.
- [ ] `api/routes/report.py`: `GET /report`.
- [ ] `api/schemas.py`: `ReportOut` and its nested shapes.
- [ ] Unit tests: one fixture event history per block (counts, approval speed with/without pull-backs, change rounds, needs attention), using a fixed `Clock`.
- [ ] Integration test: Firestore emulator, end-to-end report over a small seeded article set.
- [ ] `pnpm gen:api`.

## Out of scope
- Search performance reporting (spec: Out of scope).
- Persisting report snapshots (spec's decision: computed on request).
