from functools import cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    PROJECT_VERSION: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    SECRET_KEY: str
    TOKEN_URL: str
    ALGORITHM: str

    model_config = SettingsConfigDict(env_file='.env')

    # class Config:
    #     env_file = ".env"


@cache
def get_settings() -> Settings:
    return Settings()
