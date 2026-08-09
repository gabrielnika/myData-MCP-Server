locals {
  # Every API this project needs; adding one here is the only change required.
  services = [
    "artifactregistry.googleapis.com", # Docker image storage
    "cloudresourcemanager.googleapis.com", # Terraform reads project/IAM metadata
    "iam.googleapis.com",              # service accounts
    "iamcredentials.googleapis.com",   # token minting for Workload Identity Federation
    "run.googleapis.com",              # Cloud Run
    "secretmanager.googleapis.com",    # myDATA credentials
    "sts.googleapis.com",              # token exchange for Workload Identity Federation
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.services)

  service            = each.value
  disable_on_destroy = false
}
