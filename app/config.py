from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Atelier Commerce API"
    database_url: str = "sqlite:///./commerce.db"
    secret_key: str = "change-this-development-secret-key"
    access_token_minutes: int = 60
    reset_token_minutes: int = 30
    lab_vulnerabilities_enabled: bool = False
    host: str = "127.0.0.1"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
