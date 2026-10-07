# T-025 Group Swagger by workflow

**Phase:** 3 · API · **Status:** done · **Size:** S
**Refs:** architecture: Server folder layout

## Goal
Swagger at `/docs` lists endpoints in the order someone uses them: create a draft, then read and edit it, then publish, then the client review. Upload sits at the start of Import, ahead of paste.

## Acceptance criteria
- [x] `/docs` sections, in order: Health, Auth, Import, Articles, Publishing, Review link, Client review.
- [x] Import lists `POST /articles/upload` before `POST /articles/paste`.
- [x] Publishing lists send for review, pull back, schedule, then retry.
- [x] A unit test locks the tag order and the operation order inside each tag.
- [x] `docs/architecture.md` records the section order.

## Tasks
- [x] `api/tags.py`: tag names and `openapi_tags`, in display order.
- [x] Tag each route. Register upload before paste.
- [x] Unit test against `app.openapi()`.
- [x] Regenerate `openapi.json`.

## Out of scope
- Reordering the endpoint tables in `docs/spec.md`. Those stay grouped by who calls them.
- Changing route behavior or paths.
