from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "digital-twin-lab"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8017
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    metrics_enabled: bool = True
    traces_enabled: bool = True
    data_dir: str = str(Path(__file__).resolve().parent / "data")
    race_command_url: str = ""
    documentation_url: str = ""
    security_policy_url: str = ""
    observability_url: str = ""
    pipelines_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
