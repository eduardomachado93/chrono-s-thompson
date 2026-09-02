from langgraph.graph import StateGraph, START, END

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
from src.chrono_s_thompson.graph.nodes.ranker import rank_events_node
from src.chrono_s_thompson.graph.nodes.correlator import correlate_modern_node
from src.chrono_s_thompson.graph.nodes.writer import write_article_node
from src.chrono_s_thompson.graph.nodes.photographer import take_photograph_node


def build_chrono_graph():
    """Builds the LangGraph workflow for the Chrono S. Thompson application."""
    workflow = StateGraph(ChronoState)

    # Adding nodes to the workflow
    workflow.add_node("fetch_events", fetch_events_node)
    workflow.add_node("rank_events", rank_events_node)
    workflow.add_node("correlate_modern", correlate_modern_node)
    workflow.add_node("photographer", take_photograph_node)
    workflow.add_node("write_article", write_article_node)

    # Defining edges to establish the flow of data between nodes
    workflow.add_edge(START, "fetch_events")
    workflow.add_edge("fetch_events", "rank_events")
    workflow.add_edge("rank_events", "correlate_modern")
    workflow.add_edge("correlate_modern", "photographer")
    workflow.add_edge("photographer", "write_article")
    workflow.add_edge("write_article", END)

    return workflow.compile()