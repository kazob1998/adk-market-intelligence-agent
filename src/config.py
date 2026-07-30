"""
Configuration & Secret Manager Integration for Google ADK Agent.
Supports Google Cloud Secret Manager for enterprise secrets management
with automatic caching and graceful fallback to environment variables.
"""

import os
from typing import Optional, Dict
from src.compat import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SecretManagerService:
    """
    Google Cloud Secret Manager client wrapper.
    Fetches secrets securely from GCP Secret Manager with local in-memory caching
    and transparent fallback to local environment variables.
    """

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "adk-market-intel-demo")
        self._cache: Dict[str, str] = {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
            except Exception:
                self._client = None
        return self._client

    def get_secret(self, secret_id: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a secret from GCP Secret Manager, falling back to os.getenv().
        """
        # 1. Check local in-memory cache
        if secret_id in self._cache:
            return self._cache[secret_id]

        # 2. Check local environment variable first for fast dev / offline execution
        env_val = os.getenv(secret_id)
        if env_val:
            self._cache[secret_id] = env_val
            return env_val

        # 3. Attempt GCP Secret Manager retrieval if client available
        client = self._get_client()
        if client and self.project_id:
            try:
                name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                self._cache[secret_id] = secret_value
                return secret_value
            except Exception:
                pass

        return default


secret_service = SecretManagerService()


class Config(BaseModel):
    project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT", "adk-market-intel-demo")
    location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Strategic Model Routing Configuration
    model_pro: str = os.getenv("MODEL_PRO", "gemini-2.5-pro")
    model_flash: str = os.getenv("MODEL_FLASH", "gemini-2.5-flash")
    model_flash_lite: str = os.getenv("MODEL_FLASH_LITE", "gemini-2.5-flash-lite")
    
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_telemetry: bool = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"
    
    # Storage & Persistence
    session_db_path: str = os.getenv("SESSION_DB_PATH", "data/sessions.db")
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "data/vector_index.json")
    
    # Feature Flags
    enable_guardrails: bool = os.getenv("ENABLE_GUARDRAILS", "true").lower() == "true"
    enable_hitl: bool = os.getenv("ENABLE_HITL", "true").lower() == "true"
    enable_pii_redaction: bool = os.getenv("ENABLE_PII_REDACTION", "true").lower() == "true"

    def get_secret(self, secret_id: str, default: Optional[str] = None) -> Optional[str]:
        return secret_service.get_secret(secret_id, default)


config = Config()
