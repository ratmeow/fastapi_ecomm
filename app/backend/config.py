from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    PG_HOST: str = Field(validation_alias="POSTGRES_HOST")
    PG_PORT: int = Field(validation_alias="POSTGRES_PORT")

    PG_USER: str = Field(validation_alias="POSTGRES_USER")
    PG_PASSWORD: str = Field(validation_alias="POSTGRES_PASSWORD")

    PG_DB: str = Field(validation_alias="POSTGRES_DB")
    PG_URL: str = ""

    # JWT_KEY: str
    # JWT_ALGORITHM: str

    class Config:
        env_file = ".env"


settings = AppSettings()
settings.PG_URL = f"postgresql://{settings.PG_USER}:{settings.PG_PASSWORD}@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"
