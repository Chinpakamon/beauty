import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    # Database
    database_url: pydantic.PostgresDsn

    # Server
    debug: bool = True
    port: int = 8000

    jwt_secret: str
    access_token_expire_hours: int = 12
    jwt_algorithm: str = "HS256"
    secret_key: str

    model_config = pydantic.ConfigDict(
            env_file=".env",
            extra="ignore",
            env_file_encoding="utf-8"
        )

settings = Settings()
