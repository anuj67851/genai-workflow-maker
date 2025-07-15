import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application-wide configuration settings.
    It automatically reads from a .env file or environment variables.
    """
    # Define your configuration variables here with type hints.
    # Pydantic will automatically read them from the environment (case-insensitive).
    OPENAI_API_KEY: str
    DATABASE_PATH: str = "workflows.db"
    DATA_DB_PATH: str = "application_data.db"
    DEFAULT_MODEL: str = "gpt-4o-mini"

    # Define directories relative to the backend root
    BACKEND_ROOT: str = os.path.dirname(__file__)
    TOOL_BUILTIN_DIR: str = os.path.join(BACKEND_ROOT, 'tools', 'builtin')
    TOOL_CUSTOM_DIR: str = os.path.join(BACKEND_ROOT, 'tools', 'custom')

    VECTOR_STORE_DIR: str = "vector_stores"
    FILE_ATTACHMENT_DIR: str = "file_attachments"

    # Pydantic-settings model configuration
    model_config = SettingsConfigDict(
        env_file='.env',         # Specifies the file to load environment variables from
        env_file_encoding='utf-8',
        extra='ignore'           # Ignore extra fields from the environment
    )

# Create a single, globally accessible instance of the settings
settings = Settings()

# Ensure necessary directories exist on startup
os.makedirs(settings.TOOL_CUSTOM_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(settings.FILE_ATTACHMENT_DIR, exist_ok=True)