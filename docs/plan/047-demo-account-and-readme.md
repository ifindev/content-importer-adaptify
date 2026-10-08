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

### README rewrite
The root `README.md` still says "Status: Phase 1", and "Getting started" is a placeholder. New sections, in order:
1. **What it is:** 3 lines. Agencies import articles written elsewhere, clients approve them through a private link with no account, and approved articles are scheduled and published to WordPress. Built for Adaptify SEO's roadmap item "Ability to import existing content".
2. **Try it:** the live web URL and the demo login.
3. **Two-minute walkthrough:**
   1. Sign in. The site `wp.aiwitharifin.com` is already there.
   2. Import: paste an article, or upload a `.docx`.
   3. Open it and click Send for review.
   4. Click Copy review link and open it in a private window. That's the client's view; no login needed. Approve the article.
   5. Back in the agency app, set a publish date at least 6 minutes ahead.
   6. Wait. The article turns Published, and its live URL opens the post on WordPress.
   7. Optional: request changes instead of approving, and see the comment in the agency app. Open the Report.
4. **Notes:**
   - The first page after a quiet period can take a few seconds (the servers wake up).
   - The demo account is shared with other reviewers.
   - Publish times must be at least 5 minutes ahead.
5. **Using your own WordPress?**
   - Use a test site, not a live one.
   - It needs HTTPS, and the REST API must not be blocked by a security plugin.
   - Create an application password under Users → Profile.
   - Other reviewers share this account and can see sites you add.
   - When you're done, delete the site under Sites, and revoke the application password in WordPress.
6. **Run it locally:** `cp .env.example .env`, `make up`, `make wp-setup`, `make agency-user`, open `http://localhost:3000`, add the local site (link to architecture "Adding the local WordPress as a site"), `make wp-cron` to publish due posts.
7. **Stack and docs:** one line on the stack; links to spec, architecture, workflow, plan.

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
- [ ] The README has the sections above. It holds no secret except the demo login.
- [ ] Someone who has never seen the app (a friend, or you in a fresh private window following only the README) gets a post live on `wp.aiwitharifin.com`.
- [ ] A phone at 375px can run the client part from the review link.
- [ ] `docs/plan/README.md`, `docs/workflow.md` and architecture updated.

## Tasks
- [ ] Create both Firebase accounts.
- [ ] Add the demo site in the live app.
- [ ] Rewrite `README.md`.
- [ ] Run the walkthrough from the README in a fresh private window, then with someone new.
- [ ] Update plan README, workflow and architecture.

## Out of scope
- Seed data and a reset script.
- Per-reviewer accounts or sandboxes (a multi-tenancy feature).
- A WordPress admin login for reviewers.
- Screenshots or a video in the README. Add them later if wanted.
