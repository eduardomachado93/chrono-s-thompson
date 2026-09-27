#src.chrono_s_thompson.graph.nodes.ranker
import json
import logging
import random
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings  # Import the settings module
from src.chrono_s_thompson.core.state import ChronoState, RankedSelection
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import CURATOR_SYSTEM_PROMPT
logger = logging.getLogger(__name__)

# Instantiate the model configured for structured extraction
llm = ChatOpenAI(
    model=settings.model_name,  # Access the model name from settings
    api_key=settings.openai_api_key, # Access the OpenAI API key from settings
    temperature=0.7
)

ranker_prompt = ChatPromptTemplate.from_messages([
    ("system", CURATOR_SYSTEM_PROMPT),
    ("user", """Reference date: {target_date}

List of available events for today:
{events_payload}

Select the best story and return the structured curation.""")
])

async def rank_events_node(state: ChronoState) -> Dict[str, Any]:
    """Ranker Node - Editorial Curation and Ranking.

    This node analyzes a batch of historical events and applies editorial judgment to select the most compelling one.
    It uses an LLM to generate a 'gonzo hook' and suggest a modern parallel for contextualization.
    Args:
        state: The current state object containing the 'batched_events' and 'target_date'.

    Returns:
        A dictionary with the key 'curated_story' populated with a RankedSelection instance.
    """
    if state.get("custom_event"):
        payload_str = json.dumps([state["custom_event"]], ensure_ascii=False, indent=2)  # Serialize the custom event as JSON
        target_date = state.get("target_date", "") # Retrieve target date from the state
    else:
        batched_events = state.get("batched_events", [])  # Retrieve raw events from the state
        target_date = state.get("target_date", "") # Retrieve target date from the state

        events_list = batched_events.events if hasattr(batched_events, "events") else (batched_events if isinstance(batched_events, list) else [])

        if not events_list:
            logger.warning("[Node: rank_events] No events available for ranking.")
            return {"curated_story": None}  # Return None if no events are provided
        logger.info(f"[Node: rank_events] Evaluating {len(events_list)} historical events for curation...")

        # dump the json to every HistoricalEvent in the list to ensure proper serialization
        payload_str = json.dumps(
            [event.model_dump() if hasattr(event, "model_dump") else event for event in events_list],
            ensure_ascii=False,
            indent=2,
        )  # Serialize Pydantic events or already-serialized dictionaries as JSON

    # Configure the chain with deterministic structured output
    structured_llm = llm.with_structured_output(RankedSelection) # Apply structured output to the LLM
    chain = ranker_prompt | structured_llm # Chain the prompt and LLM

    try:
        result = await chain.ainvoke({
            # Invoke the chain with the provided context
            "target_date": target_date,
            "events_payload": payload_str
        })
        curated_story = RankedSelection.model_validate(result)

        logger.info(
            f"[Node: rank_events] Selected event ({curated_story.selected_event.year}): '{curated_story.selected_event.title}' | Hook: '{curated_story.gonzo_hook}'"
        )

        return {"curated_story": curated_story}  # Return the curated story as a dictionary
    except Exception as exc:
        logger.error(f"[Node: rank_events] Failure to process structured output from the ranker: {exc}", exc_info=True) # Log any exceptions that occur during processing
        return {"curated_story": None}  # Return None in case of an error