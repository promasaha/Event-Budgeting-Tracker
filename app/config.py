from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, populated from environment variables (or a
    local .env file in development). In AWS Lambda, these are set as function
    environment variables.
    """

    # No defaults: every value here must come from .env (local dev) or real
    # environment variables (AWS Lambda, with secrets pulled from Secrets
    # Manager). Startup fails loudly if any are missing, instead of silently
    # falling back to a known value.
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # Clients must send this in the X-API-Key header.
    api_key: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
