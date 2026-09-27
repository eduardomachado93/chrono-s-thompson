"""
This module defines the workflow for the Chrono S. Thompson application using LangGraph's StateGraph.
It sets up the nodes and edges that represent the sequence of operations in the application, including fetching
"""
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy, TimeoutPolicy

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.nodes import *

def build_chrono_graph():
    """Builds the LangGraph workflow for the Chrono S. Thompson application."""

    # 1. Função pura de decisão: lê o state e decide o próximo passo
    def check_error_and_route(next_node: str):
        def route(state: ChronoState) -> str:
            if state.error:
                return END
            return next_node
        return route

    workflow = StateGraph(ChronoState)

    # 2. Registro dos nós
    workflow.add_node("fetch_events", fetch_events_node)
    workflow.add_node("batch_events", batch_events_node)
    workflow.add_node("rank_events", rank_events_node)
    workflow.add_node("photographer", take_photograph_node)
    workflow.add_node("index_selected_event", index_selected_event)
    workflow.add_node("write_article", write_article_node)

    # 3. Início
    workflow.add_edge(START, "fetch_events")

    # 4. Transições condicionais validando o State após cada nó
    pipeline = [
        ("fetch_events", "batch_events"),
        ("batch_events", "rank_events"),
        ("rank_events", "photographer"),
        ("photographer", "index_selected_event"),
        ("index_selected_event", "write_article"),
    ]

    for current_node, next_node in pipeline:
        workflow.add_conditional_edges(
            current_node,
            check_error_and_route(next_node),
            {
                next_node: next_node,
                END: END
            }
        )

    # Último nó vai para END (ou também pode passar por validação se necessário)
    workflow.add_edge("write_article", END)

    return workflow.compile()