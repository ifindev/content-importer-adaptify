# T-003 Next.js scaffold

**Phase:** 1 · Bootstrap · **Status:** done · **Size:** S
**Refs:** architecture: Frontend › Folder layout, Rules
**Depends on:** T-001

## Goal
A Next.js app in `web/` with the agreed `app/` + `modules/` structure and every route in place, so later tickets only fill in modules.

## Acceptance criteria
- [x] `pnpm dev` serves every route in the folder layout: `/import`, `/articles`, `/articles/[id]`, `/report`, `/login`, `/review/[token]`, `/review/[token]/articles/[id]`
- [x] Every route file only imports and renders its module page (thin routes); each module page renders a placeholder heading
- [x] `(agency)/layout.tsx` and the review pages use separate layouts (review has no agency navigation)
- [x] `pnpm build` and `pnpm lint` pass
- [x] `@/*` import alias works

## Tasks
- [x] `pnpm create next-app web` with TypeScript, App Router, ESLint, Tailwind, no `src/` dir, alias `@/*`
- [x] Remove the starter page content and assets
- [x] Create `modules/{articles,review,report,auth}/{pages,components,repository,schemas}` (only folders a stub uses get files now)
- [x] Route files under `app/` per the folder layout, each rendering a module page stub (`ImportPage`, `ArticlesPage`, `ArticleDetailPage`, `ReportPage`, `LoginPage`, `ReviewPage`, `ReviewArticlePage`)
- [x] `app/(agency)/layout.tsx` with a placeholder nav (Import, Articles, Report)
- [x] Root `/` redirects to `/articles`
- [x] Makefile target: `web` (run dev server)

## Out of scope
- shadcn, Prettier, zod, API client (T-004)
- Auth guard (Phase 4)
