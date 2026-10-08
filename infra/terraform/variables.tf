variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "github_repo" {
  description = "owner/name of the repo allowed to deploy"
  type        = string
}

variable "agency_emails" {
  description = "Comma-separated emails allowed to sign in (AGENCY_EMAILS). Pass with -var or a local *.auto.tfvars."
  type        = string
}
