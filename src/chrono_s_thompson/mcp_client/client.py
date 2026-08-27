import json
import logging
import os
import sys
from typing import Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    pass


class ChronoMCPClient:
    def __init__(self) -> None:
        # Encontra a raiz do projeto (onde está o pyproject.toml / .env)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Sobe de mcp_client -> chrono_s_thompson -> src -> raiz
        project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

        env = dict(os.environ)
        # Garante que o Python encontre o pacote na raiz
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{os.path.join(project_root, 'src')}"

        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.chrono_s_thompson.mcp_server.server"],
            env=env
        )

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)

                    if not result.content:
                        return None

                    first_content = result.content[0]
                    if hasattr(first_content, "text"):
                        try:
                            return json.loads(first_content.text)
                        except json.JSONDecodeError:
                            return first_content.text

                    return first_content

        except Exception as exc:
            logger.error(f"Erro ao executar a tool '{tool_name}' no MCP Server: {exc}", exc_info=True)
            raise MCPClientError(f"Falha na execução do MCP ({tool_name}): {exc}") from exc

    async def get_historical_events(self, date_str: str) -> List[dict]:
        data = await self.call_tool("get_historical_events", {"date": date_str})
        if isinstance(data, list):
            return data
        return []