import json
import logging
import os
from posixpath import sep
import sys
from typing import Any, List

from fastmcp.client import Client, StdioTransport

from src.config.settings import settings

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    pass


import subprocess

def _get_safe_errlog() -> Any:
    """Returns a safe error stream with support for fileno() to avoid errors on Windows/Jupyter."""
    try:
        if hasattr(sys.stderr, "fileno"):
            sys.stderr.fileno()
            return sys.stderr
    except Exception:
        pass

    try:
        if hasattr(sys, "__stderr__") and sys.__stderr__ is not None and hasattr(sys.__stderr__, "fileno"):
            sys.__stderr__.fileno()
            return sys.__stderr__
    except Exception:
        pass

    return subprocess.DEVNULL


class ChronoMCPClient:
    def __init__(self) -> None:
        # Gets the project root and centralized settings via settings.py
        project_root = settings.project_root
        # Copies environment variables already loaded by settings.py
        env = dict(os.environ)

        # Ensures that Python finds the project packages at the root and in the src directory
        src_path = project_root / "src"
        env["PYTHONPATH"] = f"{project_root}{sep}{src_path}"  # Use osep for cross-platform compatibility

        # Defines the Python executable (sys.executable if mcp_python_path is 'python')
        python_cmd = (
            sys.executable
            if settings.mcp_python_path == "python"
            else settings.mcp_python_path
        )

        self.transport = StdioTransport(
            command=python_cmd,
            args=["-m", "src.chrono_s_thompson.mcp_server.server"],
            env=env,
            log_file=_get_safe_errlog()
        )

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Calls a specific tool on the MCP server.

        Args:
            tool_name (str): The name of the tool to execute.
            arguments (dict[str, Any]): A dictionary containing the arguments for the tool.

        Returns:
            Any: The result of the tool execution.  The type depends on the specific tool's output format.
                 Returns None if the tool returns no content or encounters an error.
        """
        try:
            async with Client(self.transport) as client:
                if not client.is_connected():
                    logger.error("The MCP Client is not connected to the server!", exc_info=True)
                    return None
                result = await client.call_tool(tool_name, arguments=arguments)

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
            logger.error(f"Error executing tool '{tool_name}' on MCP Server: {exc}", exc_info=True)
            raise MCPClientError(f"MCP execution failure ({tool_name}): {exc}") from exc


    async def get_historical_events(self, date_str: str) -> List[dict]:
        """
        Retrieves historical events for a given date.

        Args:
            date_str (str): The date to retrieve events for in MM/DD format.
        Returns:
            List[dict]: A list of dictionaries representing the historical events, or an empty list if no events are found.
        """
        data = await self.call_tool("get_historical_events", {"date": date_str})
        if isinstance(data, list):
            return data
        return []

