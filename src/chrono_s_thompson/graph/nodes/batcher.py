#src.chrono_s_thompson.graph.nodes.batcher
from collections.abc import Iterator
import json
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
    if isinstance(e, dict):
        return e.get("year", 0), e.get("page_name", "")
    return getattr(e, "year", 0), getattr(e, "page_name", "")

async def batch_events_node(state: ChronoState) -> Dict[str, Any]:
    raw_events = state.raw_events # Retrieve raw events from the state
    if not raw_events:
        return {"error": True, "error_msg": "[Node: rank_events] No events available for ranking."}
    if state.custom_event:
        return {"batched_events": EventList(events=[state.custom_event])}
    else:
        logger.info(f"[Node: rank_events] Evaluating {len(raw_events)} historical events for curation...")
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
                logger.info(f"[Node: rank_events] Selected {len(candidates)} historical events for curation...")
                logger.info(candidates)
            return {"batched_events": EventList(events=candidates)}  # Return the best ranked candidates
        except Exception as exc:
            logger.error(f"[Node: rank_events] Failure to process structured output from the ranker: {exc}", exc_info=True) # Log any exceptions that occur during processing
            fallback_events = [
                e if isinstance(e, HistoricalEvent) else HistoricalEvent.model_validate(e)
                for e in raw_events[:10]
            ]
            return {"batched_events": EventList(events=fallback_events)}  # Return the first 10 events in case of error

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