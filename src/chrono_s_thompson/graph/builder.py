"""
This module defines the workflow for the Chrono S. Thompson application using LangGraph's StateGraph.
It sets up the nodes, retry/timeout policies, and conditional transitions that represent the end-to-end
sequence of operations, handling error routing gracefully across all steps.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy, TimeoutPolicy

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.nodes import *


def build_chrono_graph():
    """Builds and compiles the LangGraph workflow for the Chrono S. Thompson pipeline."""

    # 1. Pure decision routing helper: inspects state and halts on errors
    def check_error_and_route(next_node: str):
        def route(state: ChronoState) -> str:
            if state.error:
                return END
            return next_node
        return route

    # Initialize the state graph with the shared ChronoState schema
    workflow = StateGraph(ChronoState)

    # 2. Node registration with retry and timeout policies
    workflow.add_node(
        "fetch_events", 
        fetch_events_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "batch_events", 
        batch_events_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "rank_events", 
        rank_events_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "photographer", 
        take_photograph_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=120)
    )
    workflow.add_node(
        "index_selected_event", 
        index_selected_event,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "write_article", 
        write_article_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )

    # 3. Entry point: start execution at the fetch_events node
    workflow.add_edge(START, "fetch_events")

    # 4. Sequential pipeline definitions with conditional error checks between nodes
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

    # 5. Final transition: route completed article generation to the graph END
    workflow.add_edge("write_article", END)

    return workflow.compile()