from typing import List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class HistoricalEvent(BaseModel):
    """Representação estruturada de um evento histórico retornado pelo MCP Server."""
    year: int = Field(description="Ano em que o evento ocorreu.")
    title: str = Field(description="Título ou manchete resumida do fato.")
    description: str = Field(description="Detalhes e extrato informativo sobre o acontecimento.")
    category: str = Field(default="História Geral", description="Categoria temática do evento.")


class RankedSelection(BaseModel):
    """Resultado da curadoria e análise editorial do agente rankeador."""
    selected_event: HistoricalEvent = Field(
        description="O evento histórico escolhido como o mais relevante e impactante."
    )
    gonzo_hook: str = Field(
        description="O ângulo caótico, urgente ou irônico sob o qual a história será narrada."
    )
    suggested_modern_topic: str = Field(
        description="Tema contemporâneo sugerido para correlacionar com o fato histórico."
    )


class ChronoState(TypedDict):
    """Estado global compartilhado entre todos os nós do LangGraph."""
    target_date: str                           # Data alvo no formato 'MM/DD'
    raw_events: List[dict]                     # Payload bruto retornado pelo MCP Server
    curated_story: Optional[RankedSelection]   # Evento selecionado e hook editorial via Pydantic
    modern_context: Optional[str]              # Resumo da correlação com a atualidade
    final_article: Optional[str]               # Matéria final redigida no estilo Gonzo
    published_path: Optional[str]              # Caminho do arquivo .md salvo em disco