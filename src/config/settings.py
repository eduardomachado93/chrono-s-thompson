#src.config.settings
"""
Application settings for the Chrono S. Thompson historian agent.
"""
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Loads environment variables from the .env file if it exists
if ENV_FILE_PATH.exists():
    load_dotenv(dotenv_path=ENV_FILE_PATH)

class Settings(BaseSettings):
    # LLM Settings
    openai_api_key: SecretStr = Field(description="API key for OpenAI integration.")
    model_name: str = Field(default="gpt-5.4-nano-2026-03-17", description="Default LLM model used by the LangGraph.")
    embedding_model_name: str = Field(default="text-embedding-3-large", description="Default embedding model for vector store operations.")
    image_model_name: str = Field(default="gpt-5.4-nano-2026-03-17", description="Default LLM model for image generation.")
    temperature: float = Field(default=0.8, description="Temperature for Gonzo-style article generation.")
    batcher_temperature: float = Field(default=0.7, description="Temperature for Gonzo-style article generation.")

    # MCP Server Settings
    mcp_server_script: Path = Field(
        default=Path("src/chrono_s_thompson/mcp_server/server.py"), 
        description="Relative path to the MCP server script."
    )
    mcp_python_path: str = Field(default="python", description="Binary path for the Python interpreter to run the MCP server via stdio.")

    # Storage & Paths
    project_root: Path = Field(default=PROJECT_ROOT, description="Absolute root path of the project.")
    output_dir: Path = Field(default=Path("storage/output"), description="Directory where articles are saved.")
    log_level: str = Field(default="INFO", description="Logging level for the application.")

    # Project Meta
    agent_name: str = Field(default="Chrono S. Thompson", description="Identity of the historian agent.")
    wikipedia_user_agent: str = Field(
        default="ChronoThompsonBot/1.0 (portfolio@dev.com)",
        description="User-Agent for requests to the Wikimedia API."
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the application settings."""
    return Settings()

settings = get_settings()