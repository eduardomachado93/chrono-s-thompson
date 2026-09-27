"""
This module contains tests for the rank_events_node.py module. It sets up a test scenario with a sample ChronoState, then calls the rank_events_node function and prints the result or any exceptions that occur.
"""
import pytest

from src.chrono_s_thompson.graph.nodes.batcher import batch_events_node
from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent, RankedSelection
from typing import Any, Dict

@pytest.mark.asyncio
async def test_batch_events() -> Dict[str, Any]:
    raw_event1 = HistoricalEvent(
                    year=1883,
                    title="Eruption of Krakatoa reaches its violent climax.",
                    page_name="The catastrophic volcanic explosion generated the loudest sound in recorded history...",
                    category="General History"
                )
    raw_event2 = HistoricalEvent(
                    year=1963,
                    title="Martin Luther King Jr. delivers his 'I Have a Dream' speech.",
                    page_name="During the March on Washington for Jobs and Freedom, Martin Luther King Jr. delivered his iconic speech...",
                    category="Civil Rights"
                )
    raw_event3 = HistoricalEvent(
                    year=1950,
                    title="The sinking of the USS Maine.",
                    page_name="The sinking of the USS Maine in Havana Harbor...",
                    category="Civil Rights"
                )   
    raw_event4 = HistoricalEvent(
                    year=324,
                    title="Constantine I wins the Battle of the Milvian Bridge, becoming the sole Roman emperor.",
                    page_name="Constantine I defeats Licinius at the Battle of the Milvian Bridge...",
                    category="Ancient Rome"
                )   
    raw_event5 = HistoricalEvent(
                    year=1789,
                    title="The storming of the Bastille.",
                    page_name="The storming of the Bastille in Paris...",
                    category="French Revolution"
                )   
    raw_event6 = HistoricalEvent(
                    year=1066,
                    title="The Battle of Hastings.",
                    page_name="The Battle of Hastings was fought between the Norman-French army of William, Duke of Normandy, and an English army under the Anglo-Saxon King Harold Godwinson...",
                    category="Medieval History"
                )   
    raw_event7 = HistoricalEvent(
                    year=1492,
                    title="Christopher Columbus reaches the Americas.",
                    page_name="Christopher Columbus reaches the Americas...",
                    category="Exploration"
                )   
    raw_event8 = HistoricalEvent(
                    year=800,
                    title="The coronation of Charlemagne.",
                    page_name="Charlemagne is crowned Emperor of the Romans...",
                    category="Medieval History"
                )   
    raw_event9 = HistoricalEvent(
                    year=509,
                    title="The establishment of the Roman Republic.",
                    page_name="The Roman Republic is established...",
                    category="Ancient Rome"
                )   
    raw_event10 = HistoricalEvent(
                    year=44, #BC
                    title="The assassination of Julius Caesar.",
                    page_name="Julius Caesar is assassinated...",
                    category="Ancient Rome"
                )   
    raw_event11 = HistoricalEvent(
                    year=1517,
                    title="Martin Luther posts his Ninety-five Theses.",
                    page_name="Martin Luther posts his Ninety-five Theses...",
                    category="Reformation"
                )   
    raw_event12 = HistoricalEvent(
                    year=1453,
                    title="The fall of Constantinople.",
                    page_name="The fall of Constantinople to the Ottoman Empire...",
                    category="Medieval History"
                )   
    raw_event13 = HistoricalEvent(
                    year=1914,
                    title="The assassination of Archduke Franz Ferdinand.",
                    page_name="The assassination of Archduke Franz Ferdinand...",
                    category="World War I"
                )   
    raw_event14 = HistoricalEvent(
                    year=476, #BC
                    title="The fall of the Western Roman Empire.",
                    page_name="The fall of the Western Roman Empire...",
                    category="Ancient Rome"
                )   
    raw_event15 = HistoricalEvent(
                    year=1215,
                    title="Magna Carta is signed.",
                    page_name="Magna Carta is signed...",
                    category="Medieval History"
                )   
    test_state: ChronoState = {
        "target_date": "08/27",
        "raw_events": [raw_event1, 
                       raw_event2, 
                       raw_event3, 
                       raw_event4, 
                       raw_event5, 
                       raw_event6, 
                       raw_event7, 
                       raw_event8, 
                       raw_event9, 
                       raw_event10, 
                       raw_event11,
                       raw_event12, 
                       raw_event13, 
                       raw_event14, 
                       raw_event15],
        "batched_events": [],
        "detailed_event": None,
        "curated_story": None,
        "final_article": None,
        "published_path": None,
        "filename": None,
        "custom_event": None,
        "retriever": None
    }
    try:
        result = await batch_events_node(test_state)
        return result
    except Exception as e:
        print(e)
        return {"batched_events": []}

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_batch_events())
    if result and "batched_events" in result and result["batched_events"]:
        print(f"Batched Event: {result['batched_events']}")
    else:
        print("No batched event found.")