# Values are added by hand with `gcloud secrets versions add`, so they never
# sit in Terraform state.
resource "google_secret_manager_secret" "secrets" {
  for_each = toset(["CREDENTIAL_ENCRYPTION_KEY", "INTERNAL_API_SECRET"])

  secret_id = each.key
  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

# Bound on each secret, not the project, so neither service can read any
# other secret in the project.
locals {
  secret_readers = {
    "api-CREDENTIAL_ENCRYPTION_KEY" = { secret = "CREDENTIAL_ENCRYPTION_KEY", sa = google_service_account.api.email }
    "api-INTERNAL_API_SECRET"       = { secret = "INTERNAL_API_SECRET", sa = google_service_account.api.email }
    "web-INTERNAL_API_SECRET"       = { secret = "INTERNAL_API_SECRET", sa = google_service_account.web.email }
  }
}

resource "google_secret_manager_secret_iam_member" "readers" {
  for_each = local.secret_readers

  secret_id = google_secret_manager_secret.secrets[each.value.secret].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value.sa}"
}
