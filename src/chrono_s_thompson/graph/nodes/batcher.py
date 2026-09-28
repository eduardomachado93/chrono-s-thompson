"""
Node responsible for batching and evaluating historical events in the Chrono S. Thompson LangGraph workflow.
"""
from collections.abc import Iterator
import asyncio
import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState, EventList, HistoricalEvent
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import SHORTLIST_PROMPT

logger = logging.getLogger(__name__)

# Instantiate the model configured for structured extraction
llm = ChatOpenAI(
    model=settings.model_name,
    api_key=settings.openai_api_key,
    temperature=settings.batcher_temperature
)
structured_llm = llm.with_structured_output(EventList)
ranker_prompt = ChatPromptTemplate.from_messages([
    ("user", SHORTLIST_PROMPT),
])
chain = ranker_prompt | structured_llm

def get_event_key(e: Any) -> tuple[int, str]:
    """Extracts a unique key (year, page_name) from a historical event object or dictionary.

    Args:
        e: Historical event object or dictionary.

    Returns:
        A tuple containing the year and page name.
    """
    if isinstance(e, dict):
        return e.get("year", 0), e.get("page_name", "")
    return getattr(e, "year", 0), getattr(e, "page_name", "")

async def batch_events_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for batching and evaluating raw historical events.

    Args:
        state: The current state of the pipeline containing `raw_events` and optionally `custom_event`.

    Returns:
        A dictionary with the key `batched_events` containing the ranked candidates, or an error payload.
    """
    raw_events = state.raw_events # Retrieve raw events from the state
    if not raw_events:
        return {"error": True, "error_msg": "[Node: batch_events] No events available for ranking."}
    if state.custom_event:
        return {"batched_events": EventList(events=[state.custom_event])}
    else:
        logger.info(f"[Node: batch_events] Evaluating {len(raw_events)} historical events for curation...")
        try:
            if len(raw_events) <= 10:
                candidates = [
                    e if isinstance(e, HistoricalEvent) else HistoricalEvent.model_validate(e)
                    for e in raw_events[:10]
                ]
            else:
                # Run a group of tasks in parallel to rank the best events
                batches = list(chunk_list(raw_events, 10))
                tasks = [filter_batch(batch) for batch in batches]
                results = await asyncio.gather(*tasks)
                # Join every best ranked event
                selected_keys = {get_event_key(e) for batch_res in results for e in batch_res.events}
                if selected_keys:
                    candidates = [e for e in raw_events if get_event_key(e) in selected_keys]
                else:
                    candidates = raw_events[:10]
                logger.info(f"[Node: batch_events] Selected {len(candidates)} historical events for curation...")
            return {"batched_events": EventList(events=candidates)}  # Return the best ranked candidates
        except Exception as exc:
            return {"error": True, "error_msg": f"[Node: batch_events] Error in batching historical events: {exc}"}

def chunk_list(items: list[Any], size: int) -> Iterator[EventList]:
    """Yields successive chunks of historical events structured as EventList objects.

    Args:
        items: List of raw historical events.
        size: The maximum size of each chunk.

    Yields:
        An EventList containing up to `size` HistoricalEvent items.
    """
    for i in range(0, len(items), size):
        chunk = items[i:i + size]
        events = [e if isinstance(e, HistoricalEvent) else HistoricalEvent.model_validate(e) for e in chunk]
        yield EventList(events=events)

async def filter_batch(batch: EventList) -> EventList:
    """Filters a batch of historical events using LLM structured extraction.

    Args:
        batch: EventList containing historical event candidates.

    Returns:
        Filtered EventList with the highest-ranked historical events.
    """
    # Format HistoricalEvent list to string format
    str_batch_formated = batch.model_dump_json(ensure_ascii=False)
    # Invoke chain with template variables
    result = await chain.ainvoke({"events_batch": str_batch_formated})
    #Validate the Model output
    if not isinstance(result, EventList):
        logger.warning("[Node: batch_events] Invalid structured output from the ranker.")
        return EventList(events=[])
    # Return structured HistoricalEvent list
    return result   