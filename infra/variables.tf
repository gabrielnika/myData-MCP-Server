variable "project_id" {
  description = "GCP project that hosts all resources."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository (owner/name) allowed to deploy via Workload Identity Federation."
  type        = string
}

variable "region" {
  description = "Region for all regional resources (Artifact Registry, Cloud Run)."
  type        = string
  default     = "europe-west1"
}
