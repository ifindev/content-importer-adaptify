# T-026 Access control and app shell

**Phase:** 4 · Frontend · **Status:** in progress · **Size:** L
**Refs:** R8.1, R8.2, spec: Screens, API endpoints; architecture: Auth, Frontend
**Depends on:** T-012, T-018

## Goal
The agency signs in once and works inside a responsive app shell with a sidebar. Logged-out visitors can't reach any agency screen. The client reaches the review pages with the token alone and never sees agency navigation.

## Analysis

### Flow: agency login
1. `/login` signs in with the Firebase JS SDK (`signInWithEmailAndPassword`). Locally it points at the Auth emulator (`connectAuthEmulator`).
2. The page gets an ID token and calls the Server Action `createSession(idToken)`.
3. `createSession` posts to `POST /auth/session` and reads the `session` value from the API's `Set-Cookie`. It sets the same value on the browser: `httpOnly`, `secure` (off when `APP_ENV=local`), `sameSite=lax`, `path=/`, 5-day max-age (matches T-012).
4. It redirects to `next` (default `/articles`). `next` is used only when it starts with `/` and not `//`, which blocks open redirects.
5. The Firebase client session is not needed after this. The page calls `signOut()` on the SDK right away, so the httpOnly cookie is the only credential.

### Flow: guard
- **`proxy.ts`** (Next 16's renamed middleware) matches `/`, `/import`, `/articles/:path*`, `/report`, `/login`.
  - No `session` cookie on an agency path → redirect to `/login?next=<path>`.
  - `/` → `/articles` with a cookie, `/login` without.
  - `/login` with a cookie → `/articles`.
  - This is an optimistic check: the cookie is present, not verified.
- **Real check:** `lib/api-server.ts` catches `ApiError` with status 401 on agency calls and calls `redirect('/login?next=…')`. An expired, revoked, or tampered cookie fails at the first query of any page. `next` comes from the request path header that `proxy.ts` sets (`x-pathname`).
  - The review client calls never get a 401 (the token routes have no session), so this only fires on agency calls.
- **Logout:** a Server Action deletes the `session` cookie and redirects to `/login`.

### Flow: client boundary
| Route | Agency logged in | Logged out / client |
| --- | --- | --- |
| `/import`, `/articles*`, `/report` | ✓ | → `/login` |
| `/review/{token}*`, valid token | ✓ (client view only) | ✓ |
| `/review/{bad or reset token}*` | generic 404 | generic 404 |

- `app/review/[token]/layout.tsx`: no sidebar and no agency links. Header with the site name (filled in T-029). `metadata.robots = { index: false, follow: false }`.
- `next.config` `headers()`: `Referrer-Policy: no-referrer` on `/review/:path*`. Without it, clicking a live-page link sends the full review URL, token included, to the client's site in the Referer header.
- `app/review/[token]/not-found.tsx`: "This link isn't valid." It never says whether the link once existed (spec decision: 404, not 403).
- A 429 `rate_limited` on review pages shows "Too many requests. Try again in a minute." through `app/review/[token]/error.tsx`, which reads the code.

### Web: shell
- shadcn components to add: `sidebar`, `sheet`, `badge`, `alert`, `sonner`, `skeleton`, `dialog`, `select`, `tabs`, `input`, `textarea`, `label`, `tooltip`, `dropdown-menu`.
- `(agency)/layout.tsx` hosts `SidebarProvider`, `AppSidebar`, `<main>`, and `<Toaster />`.
- Breakpoints:

| Width | Sidebar |
| --- | --- |
| < `md` (768px) | Hidden. Top bar with a hamburger opens the sidebar in a Sheet. The Sheet closes on navigation. |
| `md`–`lg` | Collapsed icon rail with tooltips. |
| ≥ `lg` | Expanded. The user can collapse it; shadcn keeps the state in its cookie. |

- Sidebar content: app name, nav (Import, Articles, Report with lucide icons, active state from `usePathname`), and a footer with the user email and Logout.
  - Email: `createSession` stores the email from the decoded ID token in a second, non-httpOnly `agency_email` cookie, display only. Skipped: a `/auth/me` endpoint. Add it when there's more than one user.
- `(agency)/loading.tsx` (skeleton), `(agency)/error.tsx` (message + retry), `(agency)/not-found.tsx`.
- Shared components in `components/`. They are domain components, not shadcn, used by articles, report, and review:
  - `StatusBadge`: 7 statuses, one color each.
  - `SyncWarningBadge`: Late, Changed in WordPress, Missing in WordPress.
  - `WordPressBanner`: "Can't reach WordPress. Statuses may be out of date."

### Local setup
- `.env.example` + compose `web` service:
  - `NEXT_PUBLIC_FIREBASE_API_KEY`, `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NEXT_PUBLIC_FIREBASE_PROJECT_ID` (`demo-content-importer`)
  - `NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL` (`http://localhost:9099`, the browser-side address)
  - `AGENCY_EMAIL`, `AGENCY_PASSWORD`
- `make agency-user`: creates the one agency account in the Auth emulator through its REST API (`accounts:signUp` with the emulator's fake key). It ignores "EMAIL_EXISTS". `make firebase-reset` wipes it, so re-run it after a reset.

### Login screen states
| State | UI |
| --- | --- |
| Default | Card with email, password, Sign in |
| Submitting | Button disabled with a spinner |
| `auth/invalid-credential` | "Wrong email or password." |
| `auth/too-many-requests` | "Too many attempts. Try again later." |
| `invalid_token` (API) | "Sign-in failed. Try again." |
| Network error | "Can't reach the server." |
| Session expired (`?next=` present) | Info line: "Please sign in again." |

### Edge cases
| Case | Behavior |
| --- | --- |
| Cookie present but expired | Proxy lets it through, the first query gets a 401, redirect to `/login?next=…` |
| `next=https://evil.com` or `//evil.com` | Ignored, goes to `/articles` |
| Agency opens a review link while logged in | Same client view; agency cookie is forwarded but the token routes ignore it |
| JS disabled on login | Not supported (Firebase SDK needs JS); acceptable for one agency user |

### Decisions
- No session-check endpoint. The first agency query is the check. Update architecture: Auth.
- `proxy.ts` is optimistic only. The layout and queries are the real guard (matches Next's auth guide).
- No server-side revoke on logout. Add it with multi-user.

## Acceptance criteria
- [x] Logged out, `/articles`, `/articles/x`, `/import`, `/report` redirect to `/login?next=…`; after login the user lands on `next`.
- [ ] A tampered `session` cookie redirects to `/login` on the first page load. Mechanism is built and code-reviewed (`lib/api-server.ts`'s 401 handling), but no page calls the API yet to exercise it live — needs T-027.
- [x] `/login` while logged in redirects to `/articles`; an external `next` is ignored.
- [x] Logout clears the cookie and agency pages redirect again.
- [ ] `/review/<valid>` works logged out, shows no sidebar, sends `Referrer-Policy: no-referrer` and `noindex`. Layout/headers verified; "valid" needs T-018's `GET /review/{token}` wired into a real page — that's T-029.
- [ ] `/review/<bad>` shows the generic 404 page. `not-found.tsx` exists; nothing calls `notFound()` yet since the review page is still a stub — needs T-029.
- [x] Sidebar: expanded at 1280px, icon rail at 768px, Sheet at 375px; keyboard can reach every nav item and Logout.
- [x] No horizontal scroll at 375, 768, 1280px on login and the shell.
- [x] `make agency-user` creates the account; running it twice is harmless.
- [x] architecture.md (Auth, Frontend) updated.

## Tasks
- [x] Design with `/design`: done on the design canvas; the visual revamp of login, shell, badges and banner moved to T-033.
- [x] `pnpm add firebase`; `lib/firebase-client.ts` (browser only, emulator when env is set).
- [x] `modules/auth`: `LoginPage`, `LoginForm` (client), `repository/auth.mutations.ts` (`createSession`, `logout`).
- [x] `proxy.ts` with the matcher and redirects, setting `x-pathname`.
- [x] `lib/api-server.ts`: 401 → `redirect('/login?next=…')`.
- [x] shadcn components; `AppSidebar`; `(agency)/layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`.
- [x] `components/status-badge.tsx`, `sync-warning-badge.tsx`, `wordpress-banner.tsx`.
- [x] `app/review/[token]/layout.tsx`, `not-found.tsx`, `error.tsx`; `next.config` headers.
- [x] `.env.example`, compose, `make agency-user`.
- [x] Unit test: the `next` sanitizer (relative path kept, `//x` and absolute URLs dropped).
- [x] Docs: architecture.md Auth + Frontend.

## Out of scope
- Multi-user, roles, password reset, server-side revoke.
- Review page content (T-033 builds it, T-029 wires it).
- Visual revamp and the `/sites/[siteId]` route restructure (T-033).
