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

# System prompt defining the role and behavior of the correlator node.
CORRELATOR_SYSTEM_PROMPT = """You are an investigative analyst specializing in tracing temporal parallels between historical events and contemporary issues.

Your task:
1. Analyze the selected historical event and provided contemporary context.
2. Identify structural similarities, ironic juxtapositions, recurring patterns, or technological/social evolution between the two eras.
3. Produce a concise, sharp, and provocative synthesis (maximum 2 paragraphs) that will serve as input for the temporal correspondent to finalize the article."""

# Prompt template for constructing the LLM query.
correlator_prompt = ChatPromptTemplate.from_messages([
    ("system", CORRELATOR_SYSTEM_PROMPT),
    ("user", """EVENT HISTORY:
- Year: {year}
- Title: {title}
- Details: {description}
- Suggested Angle: {hook}

CONTEMPORARY / NEWS CONTEXT:
{news_context}

Trace the temporal parallel, highlighting how this dynamic reflects in today's world.""")
])


# Asynchronous function to search for contemporary news via the Tavily API.
async def _search_contemporary_news(query: str) -> str:
    """Searches for recent news using the Tavily API if the key is configured."""
    if not settings.tavily_api_key:
        logger.info("[Node: correlator] Tavily API key not configured. Using base knowledge synthesis from the model.")
        return f"Contemporary topic under discussion: {query}"

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

            # Prioritize the synthesized answer from Tavily if available
            if data.get("answer"):
                return data["answer"]

            results = data.get("results", [])
            snippets = [f"- {item.get('title')}: {item.get('content')}" for item in results]
            return "\n".join(snippets) if snippets else f"Search query: {query}"

    except Exception as exc:
        logger.warning(f"[Node: correlator] Tavily API search failure ({exc}). Proceeding without external search.")
        return f"Contemporary topic of reference: {query}"


# Asynchronous function to correlate the historical event with contemporary issues.
async def correlate_modern_node(state: ChronoState) -> Dict[str, Any]:
    """Correlates the selected historical event with current themes.
    Args:
        state: State containing 'curated_story'.

    Returns:
        A dictionary with the key 'modern_context' for the ChronoState.
    """
    curated_story = state.get("curated_story")
    if not curated_story:
        logger.warning("[Node: correlator] No curated story available for correlation.")
        return {"modern_context": "No historical event selected for correlation."}

    event = curated_story.selected_event
    modern_topic = curated_story.suggested_modern_topic
    hook = curated_story.gonzo_hook

    logger.info(f"[Node: correlator] Searching for contemporary parallels for: '{modern_topic}'")

    # 1. Retrieve the current news context
    news_context = await _search_contemporary_news(modern_topic)

    # 2. Synthesize the historical parallel with the LLM
    chain = correlator_prompt | llm  # Chain the prompt and LLM
    try:
        response = await chain.ainvoke({
            "year": event.year,
            "title": event.title,
            "description": event.description,
            "hook": hook,
            "news_context": news_context
        })

        modern_context_text = response.content
        logger.info("[Node: correlator] Contemporary synthesis generated successfully.")

        return {"modern_context": modern_context_text}

    except Exception as exc:
        logger.error(f"[Node: correlator] Error generating contemporary correlation: {exc}", exc_info=True)
        return {"modern_context": f"Thematic parallel regarding {modern_topic}."}
