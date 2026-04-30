from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "retailguard"
    SECRET_KEY: str = "retailguard-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL: str = ""
    FRAUD_THRESHOLD: float = 0.7
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
