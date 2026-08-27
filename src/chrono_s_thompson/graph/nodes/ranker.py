import json
import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState, RankedSelection

logger = logging.getLogger(__name__)

# Instância do modelo configurada para extração estruturada
llm = ChatOpenAI(
    model=settings.model_name,
    api_key=settings.openai_api_key.get_secret_value(),
    temperature=0.7
)

CURATOR_SYSTEM_PROMPT = """Você é o editor-chefe de uma redação investigativa e irreverente de correspondência temporal (estilo Jornalismo Gonzo).
Sua missão é analisar uma lista de fatos históricos ocorridos no dia de hoje e selecionar o acontecimento de MAIOR impacto humano, absurdo político, revolução cultural ou tensão dramática.

CRITÉRIOS DE ESCOLHA:
1. Rejeite fatos burocráticos ou mornos (ex: tratados protocolares, inaugurações vazias).
2. Priorize eventos com alta voltagem dramática, disputas passionais, descobertas disruptivas ou contradições humanas evidentes.
3. Formule um 'gonzo_hook' ácido, urgente e provocador — o ângulo pelo qual o repórter em campo deve cobrir a história.
4. Sugira um 'suggested_modern_topic' para servir de ponte temática com as manchetes e dilemas do mundo contemporâneo.

Você DEVE preencher rigorosamente todos os campos do schema de saída."""

ranker_prompt = ChatPromptTemplate.from_messages([
    ("system", CURATOR_SYSTEM_PROMPT),
    ("user", """Data de referência: {target_date}

Lista de eventos disponíveis na data de hoje:
{events_payload}

Selecione a melhor história e devolva a curadoria estruturada.""")
])


async def rank_events_node(state: ChronoState) -> Dict[str, Any]:
    """Nó de curadoria e ranqueamento editorial do LangGraph.

    Args:
        state: Estado atual contendo a lista 'raw_events' e 'target_date'.

    Returns:
        Dicionário com a chave 'curated_story' preenchida com a instância de RankedSelection.
    """
    raw_events = state.get("raw_events", [])
    target_date = state.get("target_date", "")

    if not raw_events:
        logger.warning("[Node: rank_events] Nenhum evento disponível para ranqueamento.")
        return {"curated_story": None}

    logger.info(f"[Node: rank_events] Avaliando {len(raw_events)} eventos históricos para curadoria...")

    # Limita o payload aos primeiros 20 eventos mais relevantes para economizar contexto
    sample_events = raw_events[:20]
    payload_str = json.dumps(sample_events, ensure_ascii=False, indent=2)

    # Configura o chain com saída estruturada determinística
    structured_llm = llm.with_structured_output(RankedSelection)
    chain = ranker_prompt | structured_llm

    try:
        curated_story: RankedSelection = await chain.ainvoke({
            "target_date": target_date,
            "events_payload": payload_str
        })

        logger.info(
            f"[Node: rank_events] Evento selecionado ({curated_story.selected_event.year}): "
            f"'{curated_story.selected_event.title}' | Hook: '{curated_story.gonzo_hook}'"
        )

        return {"curated_story": curated_story}

    except Exception as exc:
        logger.error(f"[Node: rank_events] Falha ao processar structured output do ranker: {exc}", exc_info=True)
        return {"curated_story": None}