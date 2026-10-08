terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
  }

  # Created by hand before the first `terraform init` (architecture: Terraform).
  backend "gcs" {
    bucket = "content-importer-adaptify-tfstate"
  }
}

# user_project_override and billing_project: the Firebase and Identity
# Platform APIs bill quota to a project and refuse calls without one.
provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}

provider "google-beta" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}

resource "google_project_service" "services" {
  for_each = toset([
    "run",
    "firestore",
    "artifactregistry",
    "secretmanager",
    "iam",
    "iamcredentials",
    "sts",
    "firebase",
    "identitytoolkit",
    "cloudresourcemanager",
    "serviceusage",
  ])

  service            = "${each.key}.googleapis.com"
  disable_on_destroy = false
}

data "google_project" "project" {}
