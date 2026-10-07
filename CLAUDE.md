# Content Importer for Adaptify SEO

## Docs to read
- `docs/spec.md`: what the system does. Source of truth for behavior.
- `docs/architecture.md`: how the code is organized, including the server import rules and the frontend structure.
- `docs/workflow.md`: how work is done: tickets, naming, Definition of Done.
- `docs/plan/README.md`: current phase and the master list of tickets.

## Rules
- Work from a ticket in `docs/plan/`. If there's none for the task, say so before starting.
- If code changes behavior or structure, update `docs/spec.md` or `docs/architecture.md` in the same change.
- When a ticket is done, set its status in the ticket header and in `docs/plan/README.md`.
- New tickets: next number in the global sequence, flat in `docs/plan/`, from `docs/plan/_template.md`.
- Commits: `feat(T-012): …`. Branches: `T-012-short-slug`.
- Never run `git commit` until the user has reviewed the changes and explicitly says to commit, in that same request. Approval of a plan that mentions committing is not commit approval — ask again once the diff is ready.
- Tooling: uv for Python (`server/`), pnpm for the web app (`web/`). Use the Makefile targets when they exist.
- Server: `core/` never imports SDKs or HTTP clients; import-linter enforces it.
- Server: external API adapters log request/response per `docs/architecture.md`'s Logging convention.
- Frontend: thin routes in `app/`, features in `modules/`; reads in Server Components, writes in Server Actions; API types are generated, never hand-written.
