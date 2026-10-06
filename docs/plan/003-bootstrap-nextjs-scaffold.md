# T-003 Next.js scaffold

**Phase:** 1 · Bootstrap · **Status:** analyzed · **Size:** S
**Refs:** architecture: Frontend › Folder layout, Rules
**Depends on:** T-001

## Goal
A Next.js app in `web/` with the agreed `app/` + `modules/` structure and every route in place, so later tickets only fill in modules.

## Acceptance criteria
- [ ] `pnpm dev` serves every route in the folder layout: `/import`, `/articles`, `/articles/[id]`, `/report`, `/login`, `/review/[token]`, `/review/[token]/articles/[id]`
- [ ] Every route file only imports and renders its module page (thin routes); each module page renders a placeholder heading
- [ ] `(agency)/layout.tsx` and the review pages use separate layouts (review has no agency navigation)
- [ ] `pnpm build` and `pnpm lint` pass
- [ ] `@/*` import alias works

## Tasks
- [ ] `pnpm create next-app web` with TypeScript, App Router, ESLint, Tailwind, no `src/` dir, alias `@/*`
- [ ] Remove the starter page content and assets
- [ ] Create `modules/{articles,review,report,auth}/{pages,components,repository,schemas}` (only folders a stub uses get files now)
- [ ] Route files under `app/` per the folder layout, each rendering a module page stub (`ImportPage`, `ArticlesPage`, `ArticleDetailPage`, `ReportPage`, `LoginPage`, `ReviewPage`, `ReviewArticlePage`)
- [ ] `app/(agency)/layout.tsx` with a placeholder nav (Import, Articles, Report)
- [ ] Root `/` redirects to `/articles`
- [ ] Makefile target: `web` (run dev server)

## Out of scope
- shadcn, Prettier, zod, API client (T-004)
- Auth guard (Phase 4)
