from functools import lru_cache
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do projeto absoluta relativa à localização deste arquivo de configuração (src/config/settings.py -> raiz)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Carrega o arquivo .env explicitamente para o os.environ
if ENV_FILE_PATH.exists():
    load_dotenv(dotenv_path=ENV_FILE_PATH)


class Settings(BaseSettings):
    # LLM Settings
    openai_api_key: SecretStr = Field(..., description="Chave de API da OpenAI para geração e curadoria.")
    model_name: str = Field(default="gpt-5.4-nano-2026-03-17", description="Modelo LLM padrão utilizado pelo LangGraph.")
    image_model_name: str = Field(default="gpt-5.4-nano-2026-03-17", description="Modelo LLM padrão para geração de imagens")
    temperature: float = Field(default=0.8, description="Temperatura para a redação em estilo Gonzo.")

    # Search / Correlation API
    tavily_api_key: Optional[SecretStr] = Field(default=None, description="Chave para busca de notícias contemporâneas.")

    # MCP Server Settings
    mcp_server_script: Path = Field(
        default=Path("src/chrono_s_thompson/mcp_server/server.py"), 
        description="Caminho relativo para o script de inicialização do servidor MCP."
    )
    mcp_python_path: str = Field(default="python", description="Binário do Python para executar o MCP via stdio.")

    # Storage & Paths
    project_root: Path = Field(default=PROJECT_ROOT, description="Caminho raiz absoluto do projeto.")
    output_dir: Path = Field(default=Path("storage/output"), description="Diretório onde os artigos são salvos.")
    log_level: str = Field(default="INFO", description="Nível de log da aplicação.")

    # Project Meta
    agent_name: str = Field(default="Chrono S. Thompson", description="Identidade do agente cronista.")
    wikipedia_user_agent: str = Field(
        default="ChronoThompsonBot/1.0 (portfolio@dev.com)",
        description="User-Agent para requisições na Wikimedia API."
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """Retorna uma instância em cache das configurações da aplicação."""
    return Settings()


settings = get_settings()
