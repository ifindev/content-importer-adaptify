# T-046 Budget alert and kill switch

**Phase:** 5 · Deploy · **Status:** analyzed · **Size:** S
**Refs:** architecture: Cost and limits; spec: Risks (kill switch)
**Depends on:** T-042

## Goal
The project can't run up a large bill. You get an email at $5, and billing is turned off at $8, as architecture "Cost and limits" says.

## Analysis

### Precondition
Find the billing account's **currency** (Billing → Account management). Budget amounts and the `costAmount` in notifications are in that currency. If it's IDR, convert $5 and $8 at today's rate and write the numbers into `terraform.tfvars`.

### Terraform: `infra/terraform/budget.tf`
- Variables: `billing_account_id`, `budget_alert_amount` ($5), `kill_switch_amount` ($8), `currency_code`.
- APIs: `billingbudgets`, `cloudbilling`, `pubsub`, `cloudfunctions`, `cloudbuild`, `eventarc`, `run` (already on).
- `google_pubsub_topic` `budget`.
- `google_billing_budget`:
  - Scoped to this project only.
  - Amount: the kill-switch amount.
  - `threshold_rules` at the alert amount and at 100%, so the default email goes to billing admins.
  - `all_updates_rule.pubsub_topic` = the topic. Budget notifications arrive several times a day with the current month's cost.
- You need `roles/billing.costsManager` (or billing admin) on the billing account to create the budget. Add it by hand if the apply fails with a permission error.

### Function: `infra/killswitch/`
`main.py` (~30 lines) and `requirements.txt` (`functions-framework`, `google-cloud-billing`).
- Cloud Functions gen2, Python 3.12, triggered by the `budget` topic, service account `killswitch`.
- Reads the message JSON: `costAmount`, `budgetAmount`, `currencyCode`.
- If `costAmount < KILL_AT` (env): log `"under limit: <cost> of <kill_at> <currency>"` and return.
- Else, if `DRY_RUN=true` (env): log `"would disable billing"` and return.
- Else: get the project's billing info; if billing is on, call `update_project_billing_info` with an empty `billing_account_name`. Log the result.
- Deployed by Terraform: a `google_storage_bucket_object` from an `archive_file` zip of the folder, and `google_cloudfunctions2_function`.
- `DRY_RUN` starts as `"true"`, a variable in tfvars. Set it to `"false"` and apply after the test below.

### Permissions for `killswitch`
Removing billing from a project needs permission on the project's billing link. Follow Google's guide "Disable billing usage with notifications". At the time of writing it grants the function's service account **Billing Account Administrator** on the billing account, or **Project Billing Manager** on the project. Use the narrowest role that works, and check it against the guide when building. If it needs a billing-account-level role, add it by hand: it's outside the project, and Terraform might not have rights there.

### What happens when it fires
- Billing is unlinked: Cloud Run, Firestore, Secret Manager and the function itself stop working. The app is down.
- Data isn't deleted right away, but GCP may delete resources if billing stays off for a long time. Re-link quickly.
- **Re-enable:** Billing → Account management → link the project again. Set `DRY_RUN`/`KILL_AT` as needed. No redeploy needed; Cloud Run serves the current revision again.

### Edge cases
| Case | Behavior |
| --- | --- |
| Billing data arrives hours late | That's why it fires at $8, not $10 (architecture Decision). |
| The function runs again after billing is off | The billing info shows billing off; it logs and returns. |
| A fake message with no `costAmount` | Logged as malformed and ignored. |
| `DRY_RUN` left at `true` | The alert email still arrives, but nothing is cut off. The acceptance criteria require `false` at the end. |

### Decisions
- Update architecture "Cost and limits": the dry-run flag, the currency note, and the re-enable steps.

## Acceptance criteria
- [ ] `terraform apply` creates the budget, the topic and the function.
- [ ] The budget shows in the console, scoped to the project, with the alert and kill amounts in the right currency.
- [ ] `gcloud pubsub topics publish budget --message '{"costAmount": 1, "budgetAmount": 8, "currencyCode": "USD"}'` → the function logs "under limit".
- [ ] With `DRY_RUN=true`, a message with `costAmount` above the limit → the function logs "would disable billing", and billing stays on.
- [ ] `DRY_RUN` set to `false` and applied.
- [ ] architecture.md updated.

## Tasks
- [ ] Check the billing currency; convert amounts if needed.
- [ ] Write `budget.tf` and `infra/killswitch/` (`main.py`, `requirements.txt`).
- [ ] Grant the `killswitch` role per Google's guide.
- [ ] Apply with `DRY_RUN=true`; run both test messages.
- [ ] Set `DRY_RUN=false`; apply.
- [ ] Update architecture.md.

## Out of scope
- A live test that actually turns billing off on this project. If you want one, do it on a throwaway project.
- Per-service quotas or rate limits beyond Cloud Run's max instances (T-042).
