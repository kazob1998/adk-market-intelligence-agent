output "cloud_run_service_url" {
  description = "Public URL of the deployed Cloud Run ADK Agent Web Application"
  value       = google_cloud_run_v2_service.agent_service.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Docker container images"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "storage_bucket_name" {
  description = "GCS bucket name for persistent memory and export artifacts"
  value       = google_storage_bucket.memory_store.name
}

output "service_account_email" {
  description = "Dedicated Service Account email"
  value       = google_service_account.agent_sa.email
}

output "secret_manager_secret_ids" {
  description = "Secret Manager secret resources provisioned"
  value = [
    google_secret_manager_secret.adk_api_key.secret_id,
    google_secret_manager_secret.session_db_secret.secret_id
  ]
}
