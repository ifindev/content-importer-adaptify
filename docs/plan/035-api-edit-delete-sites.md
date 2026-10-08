# T-035 Edit and delete sites

**Phase:** 4 · API · **Status:** done · **Size:** M
**Refs:** spec: Screens (Sites), API endpoints
**Depends on:** T-031

## Goal
The agency can fix a site's name or WordPress details, and remove a client site it no longer manages, so the sites list and switcher stay accurate.

## Analysis

### API
`PATCH /sites/{siteId}`

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string? | Not empty when given. |
| `wp_base_url` | string? | `https://` URL. |
| `wp_username` | string? | Not empty when given. |
| `wp_app_password` | string? | Omitted or empty keeps the stored password. |

| Case | Status | Body |
| --- | --- | --- |
| Saved | 200 | `SiteOut` |
| URL, username or password changed and the WordPress test fails | 422 | `{"code": "wp_connection_failed"}`, nothing saved |
| Nothing to change | 422 | `{"code": "empty_update"}` |
| Unknown site | 404 | `{"code": "site_not_found"}` |

`DELETE /sites/{siteId}`

| Case | Status | Body |
| --- | --- | --- |
| Deleted | 204 | — |
| Unknown site | 404 | `{"code": "site_not_found"}` |

### Data changes
- Edit: a changed password is encrypted like on create.
- Delete: hard delete of the site document, every article under it with its events, and its review token hash. Nothing in WordPress is changed: published posts stay live, and scheduled posts still publish on their date.

### Core
- `edit_site`: merges the fields (an unchanged URL or username counts as no change); if `wp_base_url`, `wp_username` or `wp_app_password` changed, tests the connection with the merged values before saving (same check as `create_site`).
- Delete has no use case: the route calls `Container.delete_site(site_id)`, which calls `SiteRepository.delete_site` (Firestore `recursive_delete` cascades articles and events) and drops the in-memory fallback's article store. The stored review token hash goes with the site document, so the old link 404s; the plaintext copy in the secret store is left behind and is harmless.

### Edge cases
| Case | Behavior |
| --- | --- |
| Client opens the old review link after delete | 404, the generic "link isn't valid" page. |
| Agency has the deleted site open in another tab | Next request returns `site_not_found`; the UI shows Not found with a link to All sites. |
| Only the name changes | No WordPress call. |

### Decisions
- Hard delete with cascade, confirmed in the UI by typing the site name. No archive or restore.
- WordPress is never touched on delete; the dialog says so.

## Acceptance criteria
- [x] PATCH saves name-only changes without calling WordPress.
- [x] PATCH with changed WordPress details tests the connection and returns `422 wp_connection_failed` without saving when it fails.
- [x] An empty password keeps the stored one.
- [x] DELETE removes the site, its articles, their events and its review token; the old review link returns 404.
- [x] Unit tests for both use cases; Firestore adapter test for the cascade.
- [x] `openapi.json` and `web/lib/api/schema.ts` regenerated.

## Tasks
- [x] `edit_site` and `delete_site` use cases with unit tests.
- [x] `SiteRepository.update_site` / `delete_site` in the port, in-memory and Firestore adapters (cascade).
- [x] Routes and error mapping.
- [x] `make gen-api`.

## Out of scope
- Archiving or restoring a site.
- Deleting or unpublishing the site's posts in WordPress.
- The UI: T-033 builds it on fixtures (`updateSite`, `deleteSite`), T-032 wires it.
