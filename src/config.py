import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT", "adk-market-intel-demo")
    location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_telemetry: bool = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"
    session_db_path: str = os.getenv("SESSION_DB_PATH", ":memory:")
    
config = Config()
