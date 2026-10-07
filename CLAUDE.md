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
- Frontend testing: Playwright (or any browser e2e suite) is out of scope for UI work, and so are new vitest tests. Verify UI changes by hand in the browser (render, 375px with no horizontal scroll, keyboard and Escape, the main flows) plus `pnpm typecheck`. If a ticket asks for either, drop it and update the ticket.

## UI design conventions
The design canvas is the source of truth (`design/canvas.html`, sources in `design/project/*.dc.html`). Read the matching board before you build or restyle a screen. These rules cover screens that have no board.

**Look.** The UI is quiet and flat: white panels on a light grey shell, thin borders, almost no shadow. Copy what is already in the codebase before inventing a new style.

**Color**
- Use the tokens in `web/app/globals.css`, never raw Tailwind palette colors (`bg-red-100`) for UI states.
- Shell background `bg-app`; panels, cards and dialogs `bg-background` or `bg-card`.
- Text is `text-foreground`, then `text-muted-foreground` for secondary text, then `text-faint` for placeholders, "—" and icons at rest.
- Statuses use only the `--status-*` pairs (`bg-status-draft text-status-draft-fg` …), through `StatusBadge` and `SyncWarningBadge`.
- Errors use the soft red alert: `border-[oklch(0.91_0.045_27.325)] bg-[oklch(0.97_0.015_27.325)] text-[oklch(0.42_0.17_27.325)]`.
- Primary blue appears only on the one primary action per screen. Every other button is `outline` or `ghost`. Destructive actions are `variant="destructive"` (soft red), never solid red.

**Borders and shadows**
- Every border is 1px `border` (the `--border` token, `oklch(0.93 0.006 264)`). No `ring-*` outlines on surfaces.
- Row dividers inside lists and tables are lighter: `border-[oklch(0.955_0.003_264)]`.
- Cards: `rounded-xl border shadow-[0_1px_2px_oklch(0_0_0/0.03)]`. The agency inset panel: `shadow-[0_1px_3px_oklch(0_0_0/0.04)]`.
- Floating layers (menus, popovers) are the only things with a real shadow: `rounded-[10px] border` plus `shadow-[0_12px_32px_-8px_oklch(0_0_0/0.18),0_2px_6px_oklch(0_0_0/0.05)]`. Dialogs use the shadcn default.
- Never use `shadow-md`, `shadow-lg` or heavier on in-page elements such as bars, cards and rows.
- Radius: 6–8px for buttons, inputs and menu items, 10px for menus, alerts and drop zones, 12px for cards and panels, 14px for dialogs.

**Typography** (Geist)
- Page title: `text-xl font-semibold tracking-tight` (15px in the mobile app bar). The subtitle under it: `text-[13px] text-muted-foreground`.
- Section heading: `text-sm font-semibold`, with an optional muted count beside it.
- Body and table text 13–13.5px, row titles `text-[13.5px] font-medium`, meta and hints 12–12.5px.
- Article bodies use `PROSE` (`components/prose.ts`) at 15.5px with a 1.75 line height.
- Numbers in tables and cards use `tabular-nums`.

**Icons**
- lucide-react only, with an outline stroke.
- Sizes: `size-4` in buttons and the toolbar, `size-3.5` in menus, meta lines and small buttons, `size-5`–`size-6` in empty states.
- Icons at rest are `text-faint` or muted. They take the text color only when active.
- An icon-only button always has an `aria-label` and a `title`.

**Components**
- Buttons default to `h-8`; use `size="sm"` (h-7) in table rows. On mobile, tap targets are at least 40–44px (`h-10`, `size-11`).
- Inputs are `h-8` on desktop and `h-10` with 15px text on mobile.
- Badges are pills, 20–22px tall. Use `StatusBadge` and `SyncWarningBadge`; don't make new badge colors.
- Lists are tables at `md`+ (36px header in muted 12px text, 52–60px rows, `hover:bg-muted/40`) and stacked rows below `md`. Don't use a horizontal scroll container.
- Empty states are centered: a 44–48px bordered icon tile, a 15px title, one muted sentence, then at most one action.
- Menus come from `components/ui/dropdown-menu.tsx`, with 32px rows, 13px text, muted icons and a red Delete item. Don't restyle them per use.
- Confirm every destructive action in a dialog. Deleting a site requires typing its name.
- Feedback for a finished mutation is a sonner toast. Errors that the user must act on show inline as the soft red alert, with the text from `messageFor(code)`.
- Dates always go through `LocalTime`.

**Layout and states**
- Agency pages: `PageHeader` (title, subtitle, actions), content padding `px-4 md:px-7`, and a `max-w-[720–760px]` column for forms and editors.
- Every screen works at 375, 768 and 1280px with no horizontal scroll.
- Every data screen has its loading, empty, error and WordPress-unreachable states, and every action has a pending state (a spinner in the button, the button disabled).
- Accessibility basics: labels on every field, visible focus (`focus-visible:ring-3 ring-ring/50`), dialogs and sheets close on Escape, `role="alert"` on errors and `role="status"` on live updates.
