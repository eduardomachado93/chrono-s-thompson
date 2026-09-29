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

    # 2. Decision routing helper after fact-checking and citation verification
    def route_after_verification(state: ChronoState) -> str:
        if state.error:
            return END
        if state.verification_result and not state.verification_result.is_valid:
            return "write_article"
        return "publish_article"

    # 3. Decision routing helper after context vector search
    def route_after_search_context(state: ChronoState) -> str:
        """Routes to rerank_context if documents were retrieved, or bypasses directly to write_article if none found."""
        if state.error:
            return END
        if len(state.retrieved_docs) < 1:
            return "write_article"
        return "rerank_context"

    # Initialize the state graph with the shared ChronoState schema
    workflow = StateGraph(ChronoState)

    # 4. Node registration with retry and timeout policies
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
        "search_context",
        search_context_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "rerank_context",
        rerank_context_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "write_article", 
        write_article_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "verify_article",
        verify_article_node,
        retry_policy=RetryPolicy(max_attempts=4),
        timeout=TimeoutPolicy(run_timeout=60)
    )
    workflow.add_node(
        "publish_article",
        publish_article_node,
        retry_policy=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(run_timeout=60)
    )

    # 5. Entry point: start execution at the fetch_events node
    workflow.add_edge(START, "fetch_events")

    # 6. Sequential pipeline definitions with conditional error checks between nodes
    pipeline = [
        ("fetch_events", "batch_events"),
        ("batch_events", "rank_events"),
        ("rank_events", "photographer"),
        ("photographer", "index_selected_event"),
        ("index_selected_event", "search_context"),
        ("rerank_context", "write_article"),
        ("write_article", "verify_article"),
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

    # 7. Context search dynamic routing: proceed to rerank_context or bypass directly to write_article
    workflow.add_conditional_edges(
        "search_context",
        route_after_search_context,
        path_map={
            "rerank_context": "rerank_context",
            "write_article": "write_article",
            END: END
        }
    )

    # 8. Verification conditional transitions: retry draft or publish
    workflow.add_conditional_edges(
        "verify_article",
        route_after_verification,
        {
            "write_article": "write_article",
            "publish_article": "publish_article",
            END: END
        }
    )

    # 9. Final transition: route published article to END
    workflow.add_conditional_edges(
        "publish_article",
        check_error_and_route(END),
        {
            END: END
        }
    )

    return workflow.compile()