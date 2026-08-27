import logging
from typing import Any, Dict

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient, MCPClientError

logger = logging.getLogger(__name__)

# Instância reutilizável do cliente MCP
mcp_client = ChronoMCPClient()


async def fetch_events_node(state: ChronoState) -> Dict[str, Any]:
    """Nó inicial do LangGraph responsável por buscar fatos históricos via MCP Server.

    Args:
        state: Estado atual do pipeline contendo ao menos `target_date` ('MM/DD').

    Returns:
        Dicionário com a chave `raw_events` para mutação parcial do ChronoState.
    """
    target_date = state.get("target_date")
    if not target_date:
        logger.error("Data alvo ('target_date') não encontrada no estado do grafo.")
        return {"raw_events": []}

    logger.info(f"[Node: fetch_events] Consultando MCP Server para o dia: {target_date}")

    try:
        events = await mcp_client.get_historical_events(target_date)
        logger.info(
            f"[Node: fetch_events] Sucesso: {len(events)} eventos históricos recuperados via MCP."
        )
        return {"raw_events": events}

    except MCPClientError as exc:
        logger.error(
            f"[Node: fetch_events] Erro ao comunicar com o MCP Server: {exc}",
            exc_info=True
        )
        # Retorna lista vazia para evitar interrupção abrupta do grafo
        return {"raw_events": []}