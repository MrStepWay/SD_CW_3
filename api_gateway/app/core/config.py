from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8'
    )
    
    ORDERS_SERVICE_URL: str = "http://orders_service:8000"
    PAYMENTS_SERVICE_URL: str = "http://payments_service:8000"

settings = Settings()