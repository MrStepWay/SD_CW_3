from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    NAME: str

    @property
    def dsn(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
        )

class RabbitMQSettings(BaseSettings):
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str

    @property
    def url(self) -> str:
        return f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter='__',
        env_file_encoding='utf-8'
    )
    
    db: DatabaseSettings
    rabbitmq: RabbitMQSettings

settings = Settings()