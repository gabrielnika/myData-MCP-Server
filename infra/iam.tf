# Least-privilege identity for the Cloud Run service: it can read exactly the
# two myDATA secrets and nothing else in the project.

resource "google_service_account" "runtime" {
  account_id   = "mydata-mcp-run"
  display_name = "Cloud Run runtime for the myDATA MCP server"
}

resource "google_secret_manager_secret_iam_member" "runtime_reads_secrets" {
  for_each  = google_secret_manager_secret.mydata
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}
