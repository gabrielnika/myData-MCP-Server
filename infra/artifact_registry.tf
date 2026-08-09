resource "google_artifact_registry_repository" "images" {
  repository_id = "mydata-mcp"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker images for the myDATA MCP server"

  # Cost hygiene: keep the last 5 images, delete anything older than 30 days,
  # so storage stays well inside the free 0.5 GB.
  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "2592000s" # 30 days
    }
  }

  depends_on = [google_project_service.apis]
}
