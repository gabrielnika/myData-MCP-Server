# IAM-authenticated by default: no run.invoker binding exists here, so all
# unauthenticated requests get 403 at Google's front end. Invoker grants are
# deliberate, separate resources.

resource "google_cloud_run_v2_service" "mcp" {
  name     = "mydata-mcp"
  location = var.region

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = 0 # scale to zero: idle costs nothing
      max_instance_count = 1 # personal use; doubles as a hard cost cap
    }

    containers {
      image = "${google_artifact_registry_repository.images.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}/mydata-mcp:dev"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name = "MYDATA_USER_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mydata["mydata-user-id"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "MYDATA_SUBSCRIPTION_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mydata["mydata-subscription-key"].secret_id
            version = "latest"
          }
        }
      }
    }
  }

  # CI deploys new images per commit; Terraform must not "correct" the image
  # back to the tag above. Terraform owns config, CI owns the running image.
  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  # Cloud Run validates secret access on deploy; make sure the IAM grants
  # exist first instead of racing them.
  depends_on = [google_secret_manager_secret_iam_member.runtime_reads_secrets]
}
