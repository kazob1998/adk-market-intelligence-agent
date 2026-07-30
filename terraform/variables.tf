variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "adk-market-intel-demo"
}

variable "region" {
  description = "Google Cloud Region for Vertex AI and Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name prefix"
  type        = string
  default     = "adk-market-intelligence-agent"
}

variable "container_image" {
  description = "Artifact Registry Docker container image URI"
  type        = string
  default     = "us-central1-docker.pkg.dev/adk-market-intel-demo/adk-repo/adk-market-intelligence-agent:latest"
}

variable "model_pro" {
  description = "Gemini Pro model identifier for Supervisor and Synthesizer"
  type        = string
  default     = "gemini-2.5-pro"
}

variable "model_flash" {
  description = "Gemini Flash model identifier for Quantitative Risk Analysis"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_flash_lite" {
  description = "Gemini Flash-Lite model identifier for Market Research retrieval"
  type        = string
  default     = "gemini-2.5-flash-lite"
}

variable "enable_hitl" {
  description = "Enable Human-in-the-Loop execution approval hooks"
  type        = bool
  default     = true
}

variable "enable_guardrails" {
  description = "Enable active runtime guardrails and prompt safety policies"
  type        = bool
  default     = true
}
