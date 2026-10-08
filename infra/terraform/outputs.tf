# T-045 copies these into GitHub repo variables.
output "project_id" {
  value = var.project_id
}

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "web_url" {
  value = google_cloud_run_v2_service.web.uri
}

output "wif_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "deployer_email" {
  value = google_service_account.deployer.email
}

# Public by design: it identifies the project, it isn't a secret.
output "firebase_api_key" {
  value = data.google_firebase_web_app_config.web.api_key
}

output "firebase_auth_domain" {
  value = data.google_firebase_web_app_config.web.auth_domain
}
