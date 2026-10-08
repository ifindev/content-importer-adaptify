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
