from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# ------------------------------------------------------------------------------
# Get the absolute path to the .env file located at the project root directory.
# Since this file (config.py) is inside src/helpers/, we go two levels up.
# ------------------------------------------------------------------------------
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

print(f"[DEBUG] Looking for .env file at: {ENV_PATH} — Exists? {ENV_PATH.exists()}")

class Settings(BaseSettings):
    """
    Defines application settings loaded from environment variables (.env file).
    Pydantic automatically reads and validates the variables based on type hints.
    """

    APP_NAME: str        # Application name (e.g., "MiniRAG")
    APP_VERSION: str     # Application version (e.g., "1.0.0")
    OPEN_API_KEY: str    # API key used for external services (e.g., OpenAI API)

    # --------------------------------------------------------------------------
    # Pydantic Settings Configuration:
    # - env_file: tells Pydantic where to load variables from
    # - env_file_encoding: ensures UTF-8 support for special characters
    # --------------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
    )


def get_settings() -> Settings:
    """
    Create and return an instance of the Settings class.
    This function can be imported anywhere to access the app configuration.
    Example usage:
        from helpers.config import get_settings
        settings = get_settings()
        print(settings.APP_NAME)
    """
    return Settings()
