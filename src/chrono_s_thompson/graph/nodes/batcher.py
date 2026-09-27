#src.chrono_s_thompson.graph.nodes.batcher
from beartype.typing import Iterator
import asyncio
import json
import logging
import random
from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from config.settings import settings  # Import the settings module
from src.chrono_s_thompson.core.state import ChronoState, EventList, HistoricalEvent
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import SHORTLIST_PROMPT

logger = logging.getLogger(__name__)

# Instantiate the model configured for structured extraction
llm = ChatOpenAI(
    model=settings.model_name,  # Access the model name from settings
    api_key=settings.openai_api_key, # Access the OpenAI API key from settings
    temperature=0.7
)
structured_llm = llm.with_structured_output(EventList)
ranker_prompt = ChatPromptTemplate.from_messages([
    ("user", SHORTLIST_PROMPT),
])
chain = ranker_prompt | structured_llm


def get_event_key(e: Any) -> tuple[int, str]:
    if isinstance(e, dict):
        return (e.get("year", 0), e.get("page_name", ""))
    return (getattr(e, "year", 0), getattr(e, "page_name", ""))


async def batch_events_node(state: ChronoState) -> Dict[str, Any]:
    raw_events = state.get("raw_events", [])  # Retrieve raw events from the state
    if not raw_events:
        logger.warning("[Node: rank_events] No events available for ranking.")
        return {"batched_events": []}  # Return None if no events are provided
    logger.info(f"[Node: rank_events] Evaluating {len(raw_events)} historical events for curation...")
    try:
        if len(raw_events) <= 10:
            candidates = raw_events
        else:
            # Se for grande, roda o filtro em lotes paralelos (chunks de 10)
            batches = list(chunk_list(raw_events, 10))
            tasks = [filter_batch(batch) for batch in batches]
            results = await asyncio.gather(*tasks)
            # Achata os eventos historicos escolhidos
            selected_keys = {get_event_key(e) for batch_res in results for e in batch_res.events}
            candidates = [e for e in raw_events if get_event_key(e) in selected_keys]
            logger.info(f"[Node: rank_events] Selected {len(candidates)} historical events for curation...")
            logger.info(candidates)
        return {"batched_events": candidates}  # Return the curated story as a dictionary
    except Exception as exc:
        logger.error(f"[Node: rank_events] Failure to process structured output from the ranker: {exc}", exc_info=True) # Log any exceptions that occur during processing
        return {"batched_events": []}  # Return None in case of an error


def chunk_list(items: list[Any], size: int) -> Iterator[EventList]:
    for i in range(0, len(items), size):
        chunk = items[i:i + size]
        events = [e if isinstance(e, HistoricalEvent) else HistoricalEvent.model_validate(e) for e in chunk]
        yield EventList(events=events)


async def filter_batch(batch: EventList) -> EventList:
    # Format HistoricalEvent list to string format
    str_batch_formated = batch.model_dump_json(ensure_ascii=False)
    # Invoke chain with template variables
    result = await chain.ainvoke({"events_batch": str_batch_formated})
    #Validate the Model output
    if not isinstance(result, EventList):
        logger.warning("[Node: rank_events] Invalid structured output from the ranker.")
        return EventList(events=[])
    # Return structured HistoricalEvent list
    return result
