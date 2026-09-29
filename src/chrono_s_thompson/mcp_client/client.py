"""
Client for the local MCP Server in the Chrono S. Thompson LangGraph workflow.
https://gofastmcp.com/getting-started/welcome
"""
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, List

from fastmcp.client import Client, StdioTransport

from src.chrono_s_thompson.core.state import DetailedEvent, HistoricalEvent
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

        # Defines the Python executable as an absolute path
        if settings.mcp_python_path == "python":
            python_cmd = sys.executable
        else:
            configured_path = Path(settings.mcp_python_path)
            if not configured_path.is_absolute():
                configured_path = (project_root / configured_path).resolve()
            if configured_path.exists():
                python_cmd = str(configured_path)
            else:
                python_cmd = sys.executable

        if python_cmd.endswith("pythonw.exe"):
            python_cmd = python_cmd[:-11] + "python.exe"

        # Ensures that Python finds the project packages at the root and in the src directory
        src_path = project_root / "src"
        existing_pythonpath = env.get("PYTHONPATH", "")
        paths_to_add = [str(project_root), str(src_path)]
        if existing_pythonpath:
            paths_to_add.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(paths_to_add)

        self.transport = StdioTransport(
            command=python_cmd,
            args=["-m", "src.chrono_s_thompson.mcp_server.server"],
            env=env,
            cwd=str(project_root),
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


    async def get_historical_events(self, date_str: str) -> List[HistoricalEvent]:
        """
        Retrieves historical events for a given date.

        Args:
            date_str (str): The date to retrieve events for in MM/DD format.
        Returns:
            List[HistoricalEvent]: A list of HistoricalEvent models representing the historical events, or an empty list if no events are found.
        """
        if len(date_str) != 5 or date_str[2] != '/':
            logger.error(f"Invalid date format: {date_str}. Expected MM/DD format.")
            return []
        data = await self.call_tool("get_historical_events", {"date": date_str})
        if isinstance(data, list):
            return [
                item if isinstance(item, HistoricalEvent) else HistoricalEvent.model_validate(item)
                for item in data
            ]
        return []

    async def get_historical_event_details(self, page_name: str) -> DetailedEvent:
        """
        Retrieves detailed information for a specific historical event.

        Args:
            page_name (str): The page name of the historical event to retrieve details for.
        Returns:
            DetailedEvent: DetailedEvent model containing title, source, url, and page_name.
        """
        data = await self.call_tool("get_historical_event_details", {"page_name": page_name})
        if isinstance(data, DetailedEvent):
            return data
        if isinstance(data, dict):
            return DetailedEvent(
                title=data.get("title") or page_name,
                source=data.get("source") or "",
                page_name=data.get("page_name") or page_name,
                url=data.get("url") or f"https://en.wikipedia.org/wiki/{page_name}",
            )
        return DetailedEvent(
            title=page_name,
            source="",
            page_name=page_name,
            url=f"https://en.wikipedia.org/wiki/{page_name}",
        )