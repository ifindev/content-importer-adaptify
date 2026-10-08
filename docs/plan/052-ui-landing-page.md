# T-052 Public landing page at "/"

**Phase:** 6 · Demo readiness · **Status:** in progress · **Size:** L
**Refs:** spec: Screens (Landing), architecture: Frontend, design: `Landing.dc.html`, `LandingMobile.dc.html`
**Depends on:** T-047

## Goal
An agency owner who opens the app's address sees what Content Importer does and can jump into the demo. Today "/" only redirects, so a signed-out visitor lands straight on a login form with no context.

## Analysis

### Flow
1. Signed out, `/` shows the landing page. "Try the live demo" and "Sign in" go to `/login`, which shows the demo login.
2. Signed in, `/` redirects to `/app`, which keeps today's behavior: the last opened site's articles, else the first site, else `/sites`.
3. After sign-in (no `next`), and on `/login` with a session, the app goes to `/app`.

### Web
- `app/page.tsx` renders `modules/landing/pages/LandingPage`. The redirect moves unchanged to `app/app/page.tsx`, outside `(agency)` so the sidebar layout doesn't run first.
- `proxy.ts`: agency paths are `/app` and `/sites/*`; `/` with a session redirects to `/app`.
- Sections, top to bottom: header, hero (headline, two CTAs, two stats, and from `lg` a logo-arrow dot matrix), product window on a halftone panel, problem (today vs with Content Importer), four-step scroll story, bento features, FAQ, closing CTA, footer.
- Type: Bricolage Grotesque headings (loaded only on this page), Geist body, Geist Mono numbers.
- The landing departs from the app UI rules on purpose: a black primary button, display headings and color halftone panels. Blue appears only inside product mocks.

### Animations
CSS first, no new dependency, all off under `prefers-reduced-motion`.
- Hero rises in on load; the arrow dots pop in along the arrow, then a pulse runs up the arrow from its tail forever; a few neighbours twinkle. The dot matrix is as tall as the hero text.
- Stacked hero: the hero stays pinned (once its bottom reaches the viewport bottom) and the rest of the page slides over it while it scales back, blurs and fades (`StackedHero`, a scroll listener, so it works without scroll-driven animation support).
- One row in the product window flips Awaiting approval → Approved.
- Halftone rings drift slowly.
- Sections fade and rise in once as they scroll into view (`Reveal`, an `IntersectionObserver`); without JS nothing is hidden.
- The header gains its border after a short scroll (`animation-timeline: scroll()`).
- Scroll story (desktop): the rail and panel stay pinned; each step takes about 80vh of scroll and swaps the panel color and card. One client component with an `IntersectionObserver`. On mobile each step sits above its own panel.
- FAQ opens smoothly where `::details-content` is supported.

### Edge cases
| Case | Behavior |
| --- | --- |
| Signed in, opens `/` | Redirect to `/app` |
| Expired cookie, opens `/` | Landing page shows; the API is never called |
| `next` missing or unsafe after login | `/app` |
| No JavaScript | Everything readable; the scroll story shows step 1 on desktop |

### Decisions
- Login stays at `/login`.
- `/app` is the agency home route. Spec and architecture updated.

## Acceptance criteria
- [ ] Signed out, `/` shows the landing page; signed in, it redirects to `/app` and on to the last site.
- [ ] Sign-in without `next` lands on `/app`.
- [ ] Matches the design boards at 375, 768 and 1280px with no horizontal scroll.
- [ ] The scroll story switches steps on scroll and from the keyboard.
- [ ] With reduced motion, nothing animates and everything is visible.
- [ ] `pnpm typecheck`, `pnpm lint` and `pnpm build` pass.

## Tasks
- [ ] Move the redirect to `/app`; update `proxy.ts` and `sanitizeNext`.
- [ ] Extract `LogoMark` and reuse it in the sidebar, login and landing.
- [ ] Build `modules/landing` sections and content.
- [ ] Animations and the scroll story.
- [ ] Update spec, architecture and the design canvas.

## Out of scope
- Analytics, a contact form, pricing, and dark mode for the landing page.
