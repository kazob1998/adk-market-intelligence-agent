provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Cloud APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])

  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
}

# 2. Artifact Registry Repository for Docker Container Images
resource "google_artifact_registry_repository" "docker_repo" {
  depends_on    = [google_project_service.apis]
  location      = var.region
  repository_id = "adk-repo"
  description   = "Docker container image repository for ADK Market Intelligence Agent"
  format        = "DOCKER"
}

# 3. Google Cloud Storage Bucket for Persistent Memory Archives & Briefing Artifacts
resource "google_storage_bucket" "memory_store" {
  depends_on                  = [google_project_service.apis]
  name                        = "${var.project_id}-adk-memory-store"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# 4. Google Cloud Secret Manager Secrets
resource "google_secret_manager_secret" "adk_api_key" {
  depends_on = [google_project_service.apis]
  secret_id  = "adk-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "session_db_secret" {
  depends_on = [google_project_service.apis]
  secret_id  = "session-db-secret"

  replication {
    auto {}
  }
}

# 5. Dedicated Least-Privilege Service Account
resource "google_service_account" "agent_sa" {
  account_id   = "adk-market-intel-sa"
  display_name = "ADK Market Intelligence Agent Service Account"
}

# Grant Vertex AI user role
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant Secret Manager Secret Accessor role
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant Cloud Storage Object Admin on memory bucket
resource "google_storage_bucket_iam_member" "storage_admin" {
  bucket = google_storage_bucket.memory_store.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.agent_sa.email}"
}

# 6. Cloud Run v2 Service Deployment
resource "google_cloud_run_v2_service" "agent_service" {
  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.docker_repo,
    google_project_iam_member.vertex_ai_user
  ]
  name     = var.app_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.agent_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "MODEL_PRO"
        value = var.model_pro
      }
      env {
        name  = "MODEL_FLASH"
        value = var.model_flash
      }
      env {
        name  = "MODEL_FLASH_LITE"
        value = var.model_flash_lite
      }
      env {
        name  = "ENABLE_GUARDRAILS"
        value = tostring(var.enable_guardrails)
      }
      env {
        name  = "ENABLE_HITL"
        value = tostring(var.enable_hitl)
      }
      env {
        name  = "SESSION_DB_PATH"
        value = "data/sessions.db"
      }

      ports {
        container_port = 8080
      }
    }
  }
}

# Public access IAM policy for Web UI demo
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.agent_service.location
  name     = google_cloud_run_v2_service.agent_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
