# T-051 Mobile article editor: keep the top bar and toolbar in view

**Phase:** 5 · Deploy · **Status:** in progress · **Size:** S
**Refs:** spec: Screens (Article detail); design canvas: `ArticleDetailMobile`
**Depends on:** —
**Improves:** T-028

## Goal
On a phone, the article page's top bar (back arrow, "Articles", status) and the formatting toolbar stay at the top while you scroll a long article. Today both scroll away, so you have to scroll back up to format text or to leave the page.

## Analysis

### Cause
`ArticleDetail.tsx` builds the page as a flex column:
- the top bar;
- the editor column (`min-w-0 flex-1 overflow-y-auto`) and the side panel;
- the mobile action bar (`sticky bottom-0`).

On desktop, the page has a fixed height (`md:h-[calc(100svh-1rem)]`), so the editor column scrolls by itself, and the toolbar's `sticky top-0` (`components/article-editor.tsx`, `Toolbar`) works.

On mobile, the page only has `min-h-svh`, so the **window** scrolls. This breaks the toolbar: a sticky element sticks inside its nearest ancestor with `overflow` set, even when that ancestor never scrolls. The editor column has `overflow-y-auto`, so the toolbar sticks to a box that doesn't move, and it scrolls away with the window. The top bar has no `sticky` at all.

The bottom action bar works because it's a direct child of the page, not inside the editor column.

### Approach
Keep the window scrolling on mobile. That keeps native scroll, and the mobile browser's address bar can still collapse. Only fix what sticks:

| Element | Change |
| --- | --- |
| Top bar (`ArticleDetail.tsx`) | `max-md:sticky max-md:top-0 max-md:z-20 bg-background`. It's 52px tall. |
| Editor column | `overflow-y-auto` → `md:overflow-y-auto`, so the toolbar's sticky container on mobile is the page. |
| Toolbar (`article-editor.tsx`) | Takes a `toolbarClassName` prop. `ArticleDetail` passes `max-md:top-[52px]`, so the toolbar sits under the top bar. The default stays `top-0`. |
| Action bar | No change: `sticky bottom-0` already works. |

`ImportForm.tsx` also uses `ArticleEditor`. Without the new prop, its toolbar keeps `top-0`, as today.

### Edge cases
| Case | Behavior |
| --- | --- |
| Article that can't be edited (Approved, Scheduled, Published, before "Edit") | No toolbar. Only the top bar sticks. |
| Status notice above the editor | Scrolls away, as today. It isn't needed while writing. |
| Feedback block and side panel below the editor on mobile | Scroll under the sticky bars, as part of the page. |
| On-screen keyboard open (iOS, Android) | The window scrolls with the caret, and the bars stay at the top of the visible area. Check by hand on a real phone or the simulator. |
| Toolbar wider than the screen | It already scrolls sideways (`overflow-x-auto`). No change. |
| Desktop (`md` and up) | Unchanged: the column scrolls, and the toolbar sticks at `top-0`. |

### Decisions
- Window scroll with sticky bars, not a fixed-height page with an inner scroll area. An inner scroll area would stop the mobile address bar from collapsing, and it behaves worse with the on-screen keyboard on iOS.
- No change to the design canvas. The `ArticleDetailMobile` board already shows the bars at the top. This ticket makes them stay there.

## Acceptance criteria
- [x] On a phone (375px), scrolling a long draft keeps the top bar and the toolbar at the top, and the action bar at the bottom.
- [x] The toolbar sits directly under the top bar, with no gap and no overlap. Text scrolls under both.
- [x] Formatting works from the sticky toolbar while scrolled down: bold, lists, link.
- [x] Read-only articles: the top bar sticks, and there's no empty toolbar space.
- [x] Desktop (768 and 1280px) and the Import paste editor are unchanged.
- [x] No horizontal scroll at 375px. `pnpm typecheck` passes.
- [ ] Checked by hand with the on-screen keyboard open, on the iOS Simulator or a phone.

## Tasks
- [x] `ArticleDetail.tsx`: make the top bar sticky on mobile; set `overflow-y-auto` on the editor column only from `md`.
- [x] `article-editor.tsx`: add `toolbarClassName` and pass it to `Toolbar`.
- [x] `ArticleDetail.tsx`: pass `max-md:top-[52px]`.
- [ ] Check by hand per the acceptance criteria.

## Out of scope
- Hiding the bars while scrolling down (the "auto-hide" pattern).
- The review page reader (`modules/review`). It has no toolbar.
