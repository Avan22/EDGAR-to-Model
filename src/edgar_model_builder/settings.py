from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    sec_user_agent: str
    sec_rps: float = 8.0
    database_url: str = "postgresql+psycopg://edgar:edgar@localhost:5432/edgar"
    redis_url: str = "redis://localhost:6379/0"
    artifacts_dir: str = "artifacts"
    marketdata_provider: str = "yfinance"

settings = Settings()
