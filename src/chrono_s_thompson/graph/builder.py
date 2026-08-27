from langgraph.graph import StateGraph, START, END

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
from src.chrono_s_thompson.graph.nodes.ranker import rank_events_node
from src.chrono_s_thompson.graph.nodes.correlator import correlate_modern_node
from src.chrono_s_thompson.graph.nodes.writer import write_article_node


def build_chrono_graph():
    """Constrói e compila a máquina de estados do Chrono S. Thompson."""
    workflow = StateGraph(ChronoState)

    # Registro dos nós
    workflow.add_node("fetch_events", fetch_events_node)
    workflow.add_node("rank_events", rank_events_node)
    workflow.add_node("correlate_modern", correlate_modern_node)
    workflow.add_node("write_article", write_article_node)

    # Fluxo linear determinístico
    workflow.add_edge(START, "fetch_events")
    workflow.add_edge("fetch_events", "rank_events")
    workflow.add_edge("rank_events", "correlate_modern")
    workflow.add_edge("correlate_modern", "write_article")
    workflow.add_edge("write_article", END)

    return workflow.compile()