terraform {
  required_version = ">= 1.10"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }

  backend "gcs" {
    # bucket comes from backend.hcl (gitignored) via:
    #   terraform init -backend-config=backend.hcl
    prefix = "mydata-mcp"
  }
}
