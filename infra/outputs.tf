output "service_url" {
  description = "HTTPS URL of the Cloud Run service (MCP endpoint is <url>/mcp)."
  value       = google_cloud_run_v2_service.mcp.uri
}

output "artifact_registry_url" {
  description = "Base URL for docker tag/push, e.g. <url>/mydata-mcp:latest"
  value       = "${google_artifact_registry_repository.images.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}
