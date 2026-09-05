from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/chatbot_ra"
    jwt_secret: str = ""
    jwt_expires_min: int = 480
    operator_email: str = ""
    operator_password: str = ""
    app_public_url: str = "http://localhost:3000"
    testing: bool = False


settings = Settings()
