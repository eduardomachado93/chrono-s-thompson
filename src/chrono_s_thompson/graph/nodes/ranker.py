import json
import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings  # Import the settings module
from src.chrono_s_thompson.core.state import ChronoState, RankedSelection

logger = logging.getLogger(__name__)

# Instantiate the model configured for structured extraction
llm = ChatOpenAI(
    model=settings.model_name,  # Access the model name from settings
    api_key=settings.openai_api_key.get_secret_value(), # Access the OpenAI API key from settings
    temperature=0.7
)

CURATOR_SYSTEM_PROMPT = """You are the editor-in-chief of an investigative and irreverent temporal correspondent newsroom (style Gonzo Journalism).
Your mission is to analyze a list of historical events occurring on today's date and select the event with the *highest* human impact, political absurdity, cultural revolution, or dramatic tension.

SELECTION CRITERIA:
1. Reject bureaucratic or mundane facts (e.g., protocol treaties, empty inaugurations).
2. Prioritize events with high dramatic voltage, passionate disputes, disruptive discoveries, or evident human contradictions.
3. Formulate an acidic, urgent, and provocative 'gonzo_hook' – the angle by which the field reporter should cover the story.
4. Suggest a 'suggested_modern_topic' to serve as a thematic bridge with contemporary headlines and dilemmas."""
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
        state: The current state object containing the 'raw_events' and 'target_date'.

    Returns:
        A dictionary with the key 'curated_story' populated with a RankedSelection instance.
    """
    if state.get("custom_event"):
        payload_str = json.dumps([state["custom_event"]], ensure_ascii=False, indent=2)  # Serialize the custom event as JSON
        target_date = state.get("target_date", "") # Retrieve target date from the state
    else:
        raw_events = state.get("raw_events", [])  # Retrieve raw events from the state
        target_date = state.get("target_date", "") # Retrieve target date from the state

        if not raw_events:
            logger.warning("[Node: rank_events] No events available for ranking.")
            return {"curated_story": None}  # Return None if no events are provided
        logger.info(f"[Node: rank_events] Evaluating {len(raw_events)} historical events for curation...")

        # Limit the payload to the first 20 most relevant events to save context
        sample_events = raw_events[:20]
        payload_str = json.dumps(sample_events, ensure_ascii=False, indent=2)  # Serialize events as JSON

    # Configure the chain with deterministic structured output
    structured_llm = llm.with_structured_output(RankedSelection) # Apply structured output to the LLM
    chain = ranker_prompt | structured_llm # Chain the prompt and LLM

    try:
        curated_story: RankedSelection = await chain.ainvoke({  # Invoke the chain with the provided context
            "target_date": target_date,
            "events_payload": payload_str
        })

        logger.info(
            f"[Node: rank_events] Selected event ({curated_story.selected_event.year}): '{curated_story.selected_event.title}' | Hook: '{curated_story.gonzo_hook}'"
        )

        return {"curated_story": curated_story}  # Return the curated story as a dictionary
    except Exception as exc:
        logger.error(f"[Node: rank_events] Failure to process structured output from the ranker: {exc}", exc_info=True) # Log any exceptions that occur during processing
        return {"curated_story": None}  # Return None in case of an error
