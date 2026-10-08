# T-039 Unschedule trashes the post, and a 5-minute minimum for publish times

**Phase:** 4 · API + UI · **Status:** done · **Size:** S
**Refs:** R4.1, R4.3; spec: Approval rules
**Depends on:** T-037
**Improves:** T-037, T-028

## Goal
Unscheduling an article leaves nothing behind in WordPress, and the agency can't schedule a time that is already past or about to be.

## Analysis

### Core
- `unschedule` calls `trash_post` (`DELETE /posts/{id}`, recoverable in WordPress's trash) before saving. A 404 counts as done: someone already removed the post. Any other WordPress error changes nothing.
- The article keeps approval, moves to Approved, and loses `wp_post_id`. The next Set date takes the create path, and the trashed post gives its slug back.
- `schedule` and `retry` refuse a publish time earlier than `now + 5 minutes` (`MIN_LEAD` in `core/use_cases/schedule.py`) with the existing `publish_at_in_past` (422). No new code or schema change.
- Articles unscheduled before this change still hold the id of a WordPress draft. If that post was deleted in WordPress, Set date and Retry used to fail with `rest_post_invalid_id` (404); they now create a new post instead. Other WordPress errors still fail the article.
- `set_draft` had no caller left, so it is removed from the port, the adapter and the scripted publisher.

### Web
- `ScheduleDialog` uses `DateTimePicker` (`components/date-time-picker.tsx`: a popover with `components/ui/calendar.tsx`, built on `react-day-picker`, and hour and minute columns, minutes in 5-minute steps; each column is a short scrolling list, because a native `<select>` opens a screen-tall menu). The browser's own `datetime-local` popup draws disabled days as grey boxes and can't be restyled, so it was dropped.
- The limit is now + 5 minutes (rounded up to a whole minute), recomputed on each open. Days before it are plain faint text on the normal background; on the first allowed day, hours before it are disabled, and in that hour so are the minutes before it. Picking that day or hour moves an earlier time up to the first allowed one. If a too-early value still gets through, the message "Pick a time at least 5 minutes from now." shows and Schedule is disabled. Submit checks again against the clock, and a server refusal shows the same message.
- A stored date that has passed (Failed) isn't used as the default; the default is tomorrow.

### Decisions
- Reverses T-037's "unschedule keeps the post as a draft". Spec, architecture and T-037 are updated.
- Trash, not permanent delete: recoverable, and the same call Delete already makes.

## Acceptance criteria
- [x] Unit tests: unschedule trashes the post and clears `wp_post_id`; a 404 on trash carries on; a refusal changes nothing; scheduling again creates a new post; now + 5 min is accepted, 4m59s is refused; Retry applies the same minimum; the route returns 422.
- [x] Integration: after unschedule the post is in WordPress's trash, and scheduling again creates a new post with the clean slug.
- [x] By hand in the browser: Unschedule shows the post in WordPress Trash; past days and earlier times are faint text with no boxes, and a time under 5 minutes away can't be picked.

## Out of scope
- Time zones other than the browser's, and times between the 5-minute steps (except the first allowed time).
