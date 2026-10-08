# If the project already has these, import them instead (architecture: Terraform).
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.services]
}

resource "google_firebase_project" "default" {
  provider = google-beta

  depends_on = [google_project_service.services]
}

resource "google_identity_platform_config" "default" {
  sign_in {
    email {
      enabled           = true
      password_required = true
    }
  }

  # The access control: nobody can sign up through the public web API key, so
  # the only accounts are the ones created in the Firebase console.
  client {
    permissions {
      disabled_user_signup = true
    }
  }

  authorized_domains = ["localhost", trimprefix(local.web_url, "https://")]

  depends_on = [google_firebase_project.default]
}

resource "google_firebase_web_app" "web" {
  provider     = google-beta
  display_name = "web"

  depends_on = [google_firebase_project.default]
}

data "google_firebase_web_app_config" "web" {
  provider   = google-beta
  web_app_id = google_firebase_web_app.web.app_id
}
