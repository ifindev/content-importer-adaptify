# T-047 Demo account and README

**Phase:** 6 · Demo · **Status:** analyzed · **Size:** S
**Refs:** R8.1; spec: User journeys; plan: Phase 6
**Depends on:** T-040, T-041, T-042, T-043, T-044, T-045, T-046

## Goal
A reviewer opens the README, signs in with the demo login, and gets an article from import to a live post on `wp.aiwitharifin.com` with no help. This is what the job application links to.

## Analysis

### Accounts
Create both in the Firebase console (Authentication → Users → Add user). Sign-up is off (T-042), so this is the only way to make an account.

| Account | Who | Password |
| --- | --- | --- |
| Your own email | You | Strong, in your password manager, never shared |
| `demo@aiwitharifin.com` | Reviewers | Strong, printed in the README. Treat it as public. |

- The demo email doesn't need a real mailbox: email/password sign-in doesn't verify it.
- Your own account means you can always get in, even if a reviewer changes the demo password through the Firebase REST API. If that happens, reset it in the console.

### The demo site
Signed in as yourself on the live app, add `https://wp.aiwitharifin.com` as a site with user `content-importer` and its Author application password (T-043). Reviewers find it ready under Sites.

### What reviewers can and can't do
- They work only in the app. They don't get the WordPress admin login.
- Published posts open on the public site through the live URL in the app. Scheduled posts stay hidden on WordPress until their date.
- They can add their own WordPress site. The README warns them about it.
- All reviewers share one agency account, so they see each other's sites and articles. That's how the product works (one agency), and the README says so.

### README: fill the demo slots
The README already tells the full story, with screenshots and animated SVGs in `docs/images/`. This ticket adds what needs the live app, at the `<!-- T-047 -->` comment under the badges:
1. **Try it:** the live web URL and the demo login.
2. **Two-minute walkthrough:**
   1. Sign in. The site `wp.aiwitharifin.com` is already there.
   2. Import: paste an article, or upload a `.docx`.
   3. Open it and click Send for review.
   4. Click Copy review link and open it in a private window. That's the client's view; no login needed. Approve the article.
   5. Back in the agency app, set a publish date at least 6 minutes ahead.
   6. Wait. The article turns Published, and its live URL opens the post on WordPress.
   7. Optional: request changes instead of approving, and see the comment in the agency app. Open the Report.
3. **Good to know:** the first page after a quiet period takes a few seconds while the servers wake up; the demo account is shared with other reviewers; publish times are at least 5 minutes ahead.
4. **Using your own WordPress?** Use a test site with HTTPS and an open REST API, create an application password under Users → Profile, and delete the site and revoke the password when you're done. Other reviewers share this account and can see sites you add.

Optionally retake the screenshots against the live app, so they show `wp.aiwitharifin.com`.

### Cleanup
By hand, through the UI, when the demo gets messy: delete stray sites and articles, re-add the demo site if someone deleted it. One line in architecture "Environments". No reset script.

### Plan and workflow docs
- `docs/plan/README.md` Phase 6 "Done when" → "Someone new signs in with the demo login and runs the full flow from the README, starting from an empty account."
- `docs/workflow.md` Phases table, Phase 6 → "README, demo account".

### Edge cases
| Case | Behavior |
| --- | --- |
| A reviewer deletes the demo site | Re-add it by hand (the steps above). Published posts stay on WordPress. |
| A reviewer changes the demo password | Reset it in the Firebase console. |
| A reviewer's own WordPress fails the connection test | The Add site dialog shows WordPress's reason (`wp_connection_failed`). The README lists the requirements. |
| Many reviewers at once | Max 2 instances per service (T-042) handle it at demo scale. |

## Acceptance criteria
- [ ] Both accounts exist; sign-up is still off.
- [ ] The demo site is on the live app, and its connection test passes.
- [ ] The README's demo slots are filled. It holds no secret except the demo login.
- [ ] Someone who has never seen the app (a friend, or you in a fresh private window following only the README) gets a post live on `wp.aiwitharifin.com`.
- [ ] A phone at 375px can run the client part from the review link.
- [ ] `docs/plan/README.md`, `docs/workflow.md` and architecture updated.

## Tasks
- [ ] Create both Firebase accounts.
- [ ] Add the demo site in the live app.
- [ ] Fill the README's demo slots.
- [ ] Run the walkthrough from the README in a fresh private window, then with someone new.
- [ ] Update plan README, workflow and architecture.

## Out of scope
- Seed data and a reset script.
- Per-reviewer accounts or sandboxes (a multi-tenancy feature).
- A WordPress admin login for reviewers.
