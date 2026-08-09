# Terraform manages the secret "envelopes" only. Values are added manually:
#   printf '%s' "$VALUE" | gcloud secrets versions add <name> --data-file=-
# so they never enter git, Terraform state, or the plan output.

locals {
  mydata_secrets = [
    "mydata-user-id",
    "mydata-subscription-key",
  ]
}

resource "google_secret_manager_secret" "mydata" {
  for_each  = toset(local.mydata_secrets)
  secret_id = each.value

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}
