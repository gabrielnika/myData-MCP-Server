# Keyless auth for GitHub Actions via Workload Identity Federation:
# GitHub's OIDC tokens are exchanged (STS) for short-lived GCP credentials.
# No service account keys exist anywhere in this setup.

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github_actions" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions"
  display_name                       = "GitHub Actions OIDC"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Reject tokens from any other repository outright.
  attribute_condition = "assertion.repository == \"${var.github_repository}\""
}

# Identity the CI pipeline acts as after the token exchange.
resource "google_service_account" "ci" {
  account_id   = "mydata-mcp-ci"
  display_name = "GitHub Actions deploy pipeline"
}

# Workflows of our repository (and only ours) may impersonate the CI SA.
resource "google_service_account_iam_member" "ci_workload_identity" {
  service_account_id = google_service_account.ci.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

# CI can push images to our repository only.
resource "google_artifact_registry_repository_iam_member" "ci_pushes_images" {
  repository = google_artifact_registry_repository.images.name
  location   = google_artifact_registry_repository.images.location
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.ci.email}"
}

# CI can deploy new revisions of this service only.
resource "google_cloud_run_v2_service_iam_member" "ci_deploys_service" {
  name     = google_cloud_run_v2_service.mcp.name
  location = google_cloud_run_v2_service.mcp.location
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.ci.email}"
}

# Deploying a service that runs as the runtime SA requires permission to
# "act as" that SA — otherwise CI could deploy code under any identity.
resource "google_service_account_iam_member" "ci_acts_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.ci.email}"
}
