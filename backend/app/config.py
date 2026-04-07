from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://venderweb:venderweb@localhost:5432/venderweb"
    database_url_sync: str = "postgresql://venderweb:venderweb@localhost:5432/venderweb"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google Places API (Capa 3)
    google_places_api_key: str = ""

    # Perplexity API (Capa 2)
    perplexity_api_key: str = ""

    # Scraping (Capa 1)
    proxy_url: str = ""
    scrape_delay_seconds: float = 10.0
    scrape_max_concurrent: int = 3

    # Auth
    jwt_secret_key: str = "change-this-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
