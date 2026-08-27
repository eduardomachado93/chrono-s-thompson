import logging
from typing import Any, Dict

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=settings.model_name,
    api_key=settings.openai_api_key.get_secret_value(),
    temperature=0.7
)

CORRELATOR_SYSTEM_PROMPT = """Você é um analista investigativo especializado em traçar paralelos temporais entre eventos do passado e o mundo contemporâneo.

Sua tarefa:
1. Analisar o evento histórico selecionado e o contexto contemporâneo fornecido.
2. Identificar semelhanças estruturais, ironias, repetições de padrões ou evoluções tecnológicas/sociais entre as duas épocas.
3. Produzir uma síntese concisa, afiada e provocadora (máximo 2 parágrafos) que servirá de insumo para o correspondente temporal finalizar o artigo.
"""

correlator_prompt = ChatPromptTemplate.from_messages([
    ("system", CORRELATOR_SYSTEM_PROMPT),
    ("user", """EVENTO HISTÓRICO:
- Ano: {year}
- Fato: {title}
- Detalhes: {description}
- Ângulo sugerido: {hook}

CONTEXTO / NOTÍCIAS CONTEMPORÂNEAS:
{news_context}

Trace o paralelo temporal destacando como essa dinâmica se reflete nos dias de hoje.""")
])


async def _search_contemporary_news(query: str) -> str:
    """Busca notícias recentes via API da Tavily caso a chave esteja configurada."""
    if not settings.tavily_api_key:
        logger.info("[Node: correlator] Tavily API key não configurada. Usando síntese baseada em conhecimento do modelo.")
        return f"Tópico contemporâneo em debate: {query}"

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key.get_secret_value(),
        "query": query,
        "search_depth": "basic",
        "max_results": 3,
        "include_answer": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # Prioriza a resposta direta sintetizada da Tavily, se existir
            if data.get("answer"):
                return data["answer"]

            results = data.get("results", [])
            snippets = [f"- {item.get('title')}: {item.get('content')}" for item in results]
            return "\n".join(snippets) if snippets else f"Pesquisa sobre: {query}"

    except Exception as exc:
        logger.warning(f"[Node: correlator] Falha na consulta Tavily ({exc}). Prosseguindo sem busca externa.")
        return f"Tópico contemporâneo de referência: {query}"


async def correlate_modern_node(state: ChronoState) -> Dict[str, Any]:
    """Nó responsável por correlacionar o fato histórico selecionado com dilemas modernos.

    Args:
        state: Estado contendo 'curated_story'.

    Returns:
        Dicionário com a chave 'modern_context' para o ChronoState.
    """
    curated_story = state.get("curated_story")
    if not curated_story:
        logger.warning("[Node: correlator] Nenhuma história curada disponível para correlação.")
        return {"modern_context": "Sem contexto histórico selecionado."}

    event = curated_story.selected_event
    modern_topic = curated_story.suggested_modern_topic
    hook = curated_story.gonzo_hook

    logger.info(f"[Node: correlator] Buscando correlações contemporâneas para: '{modern_topic}'")

    # 1. Recupera o contexto de notícias atuais
    news_context = await _search_contemporary_news(modern_topic)

    # 2. Sintetiza o paralelo histórico com o LLM
    chain = correlator_prompt | llm

    try:
        response = await chain.ainvoke({
            "year": event.year,
            "title": event.title,
            "description": event.description,
            "hook": hook,
            "news_context": news_context
        })

        modern_context_text = response.content
        logger.info("[Node: correlator] Síntese contemporânea gerada com sucesso.")

        return {"modern_context": modern_context_text}

    except Exception as exc:
        logger.error(f"[Node: correlator] Erro ao sintetizar correlação moderna: {exc}", exc_info=True)
        return {"modern_context": f"Paralelo temático com debates atuais sobre {modern_topic}."}