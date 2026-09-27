"""
This module defines the workflow for the Chrono S. Thompson application using LangGraph's StateGraph.
It sets up the nodes and edges that represent the sequence of operations in the application, including fetching
"""
from langgraph.graph import StateGraph, START, END

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
from src.chrono_s_thompson.graph.nodes.ranker import rank_events_node
from src.chrono_s_thompson.graph.nodes.writer import write_article_node
from src.chrono_s_thompson.graph.nodes.photographer import take_photograph_node
from src.chrono_s_thompson.graph.nodes.indexer import index_selected_event
from src.chrono_s_thompson.graph.nodes.batcher import batch_events_node


def build_chrono_graph():
    """Builds the LangGraph workflow for the Chrono S. Thompson application."""
    workflow = StateGraph(ChronoState)

    # Adding nodes to the workflow
    workflow.add_node("fetch_events", fetch_events_node)
    workflow.add_node("batch_events", batch_events_node)
    workflow.add_node("rank_events", rank_events_node)
    workflow.add_node("photographer", take_photograph_node)
    workflow.add_node("write_article", write_article_node)
    workflow.add_node("index_selected_event", index_selected_event)

    # Defining edges to establish the flow of data between nodes
    workflow.add_edge(START, "fetch_events")
    workflow.add_edge("fetch_events", "batch_events")
    workflow.add_edge("batch_events", "rank_events")
    workflow.add_edge("rank_events", "photographer")
    # workflow.add_edge("rank_events", "index_selected_event")
    workflow.add_edge("photographer", "index_selected_event")
    workflow.add_edge("index_selected_event", "write_article")
    workflow.add_edge("write_article", END)

    return workflow.compile()