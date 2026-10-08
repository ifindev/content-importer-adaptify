resource "google_artifact_registry_repository" "app" {
  repository_id = "app"
  location      = var.region
  format        = "DOCKER"

  # Keeps storage under the 0.5 GB free tier. KEEP wins over DELETE.
  cleanup_policy_dry_run = false
  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }
  cleanup_policies {
    id     = "delete-rest"
    action = "DELETE"
    condition {
      tag_state = "ANY"
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_service_account" "api" {
  account_id   = "api-run"
  display_name = "Cloud Run API"
}

resource "google_service_account" "web" {
  account_id   = "web-run"
  display_name = "Cloud Run web"
}

resource "google_project_iam_member" "api" {
  for_each = toset([
    "roles/datastore.user",
    # Creates session cookies and reads the user for check_revoked=True.
    "roles/firebaseauth.admin",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Cloud Run URLs are deterministic, so each service can know the other's URL
# without a dependency cycle.
locals {
  api_url = "https://api-${data.google_project.project.number}.${var.region}.run.app"
  web_url = "https://web-${data.google_project.project.number}.${var.region}.run.app"
  # Placeholder until the deploy workflow (T-045) ships the real images.
  hello_image = "us-docker.pkg.dev/cloudrun/container/hello"
}

resource "google_cloud_run_v2_service" "api" {
  name                = "api"
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.api.email

    # Max 2 caps cost and abuse; min 0 keeps it in the free tier.
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = local.hello_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "APP_ENV"
        value = "gcp"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "WEB_BASE_URL"
        value = local.web_url
      }
      dynamic "env" {
        for_each = ["CREDENTIAL_ENCRYPTION_KEY", "INTERNAL_API_SECRET"]
        content {
          name = env.value
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.secrets[env.value].secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  # The deploy workflow owns the image; apply must not roll it back.
  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_secret_manager_secret_iam_member.readers]
}

resource "google_cloud_run_v2_service" "web" {
  name                = "web"
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.web.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = local.hello_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "APP_ENV"
        value = "gcp"
      }
      env {
        name  = "API_URL"
        value = local.api_url
      }
      env {
        name = "INTERNAL_API_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["INTERNAL_API_SECRET"].secret_id
            version = "latest"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_secret_manager_secret_iam_member.readers]
}

# Both public. The web calls the API from its server with the session cookie
# and INTERNAL_API_SECRET; a private API needing ID tokens is out of scope.
resource "google_cloud_run_v2_service_iam_member" "public" {
  for_each = {
    api = google_cloud_run_v2_service.api.name
    web = google_cloud_run_v2_service.web.name
  }

  name     = each.value
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
