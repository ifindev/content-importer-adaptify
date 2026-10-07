# T-014 Import articles

**Phase:** 3 · API · **Status:** done · **Size:** M
**Refs:** R1.1–R1.7, spec: Import, API endpoints (Agency)
**Depends on:** T-013

## Goal
The agency creates a Draft article by pasting HTML, or one Draft per uploaded `.docx` file, with formatting cleaned and images flagged.

## Analysis

### Flow
1. `POST /articles/paste`: body HTML goes through `DocumentParser.clean_html` (strip disallowed tags/attrs, detect images → warning), creates one `Article` in `Draft`, `source: "paste"`.
2. `POST /articles/upload`: one or more `.docx` files; each goes through `DocumentParser.parse_docx` (mammoth → HTML, then the same cleaning), creates one `Article` per file, `source: "docx"`, `source_filename` set. One file's failure doesn't block the others — each result reports success/error independently.
3. Title: first heading if present, else (upload) the file name without extension, else (paste) `"Untitled"`. The used heading is removed from the body (R1.5). If every remaining heading shares one level, they're promoted to section headings under the title (R1.6, P1 — do if time allows within this ticket's size budget, else split out as a follow-up ticket; see Decisions).
4. Each created article gets one `imported` event.

### API
`POST /articles/paste`

| Field | Type | Rules |
| --- | --- | --- |
| `html` | string | required, non-empty after stripping tags, raw body capped at 2 MB |

`POST /articles/upload` — multipart, `files: UploadFile[]`, each must be `.docx` (checked by extension and MIME type), max 10 files per request, each file capped at 10 MB.

| Case | Status | Body |
| --- | --- | --- |
| Paste OK | 201 | `ArticleDetail` |
| Paste: empty after cleaning | 422 | `{code: "empty_content"}` |
| Paste: body over 2 MB | 413 | `{code: "payload_too_large"}` |
| Upload OK (all files) | 201 | `{results: [{filename, ok: true, article: ArticleSummary} \| {filename, ok: false, code}]}` |
| Upload: no files | 422 | `{code: "no_files"}` |
| Upload: more than 10 files | 422 | `{code: "too_many_files"}` |
| Upload: a file over 10 MB | per-file `ok: false, code: "file_too_large"` (not a request-level error — other files still process) |
| Upload: non-`.docx` file | per-file `ok: false, code: "unsupported_file_type"` (not a request-level 422 — other files still process) |

### Data changes
No schema change beyond T-013's `Article` (`warnings: list[str]`, `source`, `source_filename` already in the model).

### Core
- `core/ports/document_parser.py`: `DocumentParser` Protocol — `clean_html(html) -> ParsedDocument`, `parse_docx(bytes, filename) -> ParsedDocument`. `ParsedDocument`: `title`, `body_html`, `warnings`.
- `core/lib/html_rules.py`: the `nh3` allowed tags/attributes list (headings, paragraphs, lists, links, bold, italic, tables).
- `core/use_cases/import_article.py`: `import_from_paste(html)`, `import_from_docx(filename, bytes)` — both call the parser, build the `Article`, save via the repository, append the `imported` event.
- `adapters/documents/parser.py`: `mammoth` + `nh3` real implementation.

### Edge cases
| Case | Behavior |
| --- | --- |
| `.docx` has images | Warning `"This document had N images. Images are not imported."`, images dropped, rest of content kept |
| `.docx` has tables | Kept (R1.7) — `nh3` allows `table`/`tr`/`td`/`th` |
| Pasted HTML has inline styles (`style="color:red"`) | Attribute stripped, tag kept if allowed |
| Mixed-level headings in one document | No promotion (R1.6 only applies when every heading shares one level) — headings stay as-is in the body |
| Corrupt or non-`.docx` binary with a `.docx` name | `mammoth` raises → per-file `ok: false, code: "unreadable_file"` |

### Decisions
- Explicit size/count caps (2 MB paste, 10 files × 10 MB upload) are enforced in FastAPI itself, not left to Next.js's `bodySizeLimit` alone — that limit protects the Next.js server, not FastAPI, which Next.js calls over plain HTTP and which has no size guard of its own otherwise. Numbers are generous for a text article (even a long one is a few hundred KB) with headroom, not tuned to a real worst case yet.

## Acceptance criteria
- [x] Pasting HTML with headings, lists, links, bold/italic, and inline styles creates a Draft article with styles stripped and structure kept.
- [x] Pasting HTML containing an `<img>` creates the article with an image warning and no `<img>` in the body.
- [x] Uploading two `.docx` files creates two Draft articles, titled from each file's first heading.
- [x] One corrupt file among several uploads fails only that file; the others still import.
- [x] A `.docx` with a table keeps the table in the cleaned HTML.
- [x] A paste over 2 MB returns 413; more than 10 files or a file over 10 MB is rejected (whole request or per-file, per the table above).
- [x] Swagger updated (openapi.json regenerated). Postman: **manual follow-up** — re-import `web/lib/api/openapi.json` into Postman per `workflow.md`, then hand-write the multipart `/articles/upload` request (Postman's own import doesn't populate multipart form fields usefully).

## Tasks
- [x] `core/lib/html_rules.py`, `core/ports/document_parser.py`.
- [x] `adapters/documents/parser.py` (mammoth + nh3).
- [x] `core/use_cases/import_article.py`.
- [x] `api/routes/imports.py`: `POST /articles/paste`, `POST /articles/upload`.
- [x] Fixture `.docx` files in `tests/fixtures/` (headings, lists, images, tables, uniform/mixed-level headings, corrupt file, plus one genuine multi-section article), generated via `scripts/generate_docx_fixtures.py`.
- [x] Unit tests: cleaning rules, title extraction, per-file error isolation, with the in-memory repository.
- [x] Route-level test: real upload against the FastAPI test client with fixture files (`tests/unit/test_imports_routes.py` — no emulator/WordPress needed, so it's a unit test, not under `tests/integration/`).
- [x] `pnpm gen:api`.

## Out of scope
- Google Docs API, URL import, CMS migration (spec: Out of scope).
- Re-linking or storing dropped images.
