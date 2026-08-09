# Usage/audit events from the server. Metadata only (tool, timing, status) —
# never myDATA payload contents; see src/mydata_mcp/audit.py.

resource "google_bigquery_dataset" "audit" {
  dataset_id  = "mydata_mcp_audit"
  location    = var.region
  description = "Usage/audit events from the myDATA MCP server (metadata only)."

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_table" "events" {
  dataset_id          = google_bigquery_dataset.audit.dataset_id
  table_id            = "events"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ts"
  }

  schema = jsonencode([
    { name = "ts", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "tool", type = "STRING", mode = "REQUIRED" },
    { name = "status", type = "STRING", mode = "REQUIRED" },
    { name = "duration_ms", type = "INTEGER", mode = "NULLABLE" },
    { name = "result_count", type = "INTEGER", mode = "NULLABLE" },
    { name = "error_type", type = "STRING", mode = "NULLABLE" },
  ])
}

# Table-level grant: the runtime SA can insert rows into this one table only.
resource "google_bigquery_table_iam_member" "runtime_writes_events" {
  dataset_id = google_bigquery_dataset.audit.dataset_id
  table_id   = google_bigquery_table.events.table_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runtime.email}"
}
