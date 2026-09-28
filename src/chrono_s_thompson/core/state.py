"""
This module defines the shared state structure for the Chrono S. Thompson LangGraph.
It includes Pydantic models for data validation and state management across nodes.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, StrictBool, FilePath
from langchain_core.vectorstores.base import VectorStoreRetriever

class HistoricalEvent(BaseModel):
    """Structured representation of a historical event returned by the MCP Server."""
    year: int = Field(description="Year in which the event occurred.")
    title: str = Field(description="Brief headline or summary of the fact.")
    page_name: str = Field(description="Title of the associated Wikipedia article.")
    category: str = Field(default="General History", description="Thematic category of the event.")

class EventList(BaseModel):
    events: list[HistoricalEvent] = Field(description="A list of historical events.")

class RankedSelection(BaseModel):
    """Result of curatorial and editorial analysis by the ranking agent."""
    selected_event: HistoricalEvent = Field(
        description="The historical event chosen as the most relevant and impactful."
    )
    gonzo_hook: str = Field(
        description="The chaotic, urgent or ironic angle under which the story will be narrated."
    )
    photo_description: str = Field(
        description="The photo description of the event."
    )
    query_string: str = Field(
        description="The query string of the event. Used for retrieve relevant context from the Vector Database."
    )

class DetailedEvent(BaseModel):
    """Detailed information about a specific historical event."""
    title: str = Field(description="Title of the historical event.")
    source: str = Field(description="Source of the information about the event.")
    page_name: str = Field(default="", description="Wikipedia page identifier.")
    url: str = Field(default="", description="Canonical URL of the Wikipedia source.")

class SourceMetadata(BaseModel):
    """Metadata and snippet of a retrieved historical source."""
    id: str = Field(description="Stable identifier for the source in this generation run, e.g. 'S1'.")
    title: str = Field(description="Title of the source Wikipedia page.")
    url: str = Field(description="Canonical URL of the source.")
    page_name: str = Field(default="", description="Wikipedia page identifier.")
    content: str = Field(default="", description="Excerpt or snippet of the source text.")

class ClaimVerification(BaseModel):
    """Fact verification status for a single historical assertion."""
    claim: str = Field(description="Factual assertion extracted from article draft.")
    status: Literal["supported", "unsupported", "contradicted"] = Field(
        description="Verification status: 'supported', 'unsupported', or 'contradicted'."
    )
    source_id: Optional[str] = Field(default=None, description="Cited source ID supporting or contradicting the claim.")
    evidence: Optional[str] = Field(default=None, description="Relevant excerpt from the source text as evidence.")

class VerificationReport(BaseModel):
    """Result of citation and factual verification review."""
    is_valid: bool = Field(description="Whether the article passed citation and factual verification.")
    cited_ids: List[str] = Field(default_factory=list, description="Citation IDs found in the article text.")
    missing_citation_ids: List[str] = Field(default_factory=list, description="Cited IDs present in text but missing from available sources.")
    claims: List[ClaimVerification] = Field(default_factory=list, description="Structured factual verification of claims.")
    feedback: Optional[str] = Field(default=None, description="Detailed feedback explaining verification failures for revision.")
    limitation_notice: str = Field(
        default="Automated LLM fact-checking is a heuristic verification layer and does not guarantee absolute historical truth.",
        description="Explicit disclaimer on automated verification limitations."
    )

class ChronoState(BaseModel):
    """Global shared state between all nodes in the LangGraph."""
    target_date: str = Field(
        default=datetime.now().strftime("%m/%d"),
        description="Target date in 'MM/DD' format"
    )
    raw_events: List[HistoricalEvent] = Field(
        default_factory=list,
        description="Raw payload returned by the MCP Server"
    )
    batched_events: EventList = Field(
        default=EventList(events=[]),
        description="Filtered payload returned by the LLM"
    )
    detailed_event: Optional[DetailedEvent] = Field(
        default=None,
        description="Detailed information about a specific historical event"
    )
    curated_story: Optional[RankedSelection] = Field(
        default=None,
        description="Selected event and editorial hook via Pydantic"
    )
    draft_article: Optional[str] = Field(
        default=None,
        description="Draft article generated prior to verification and publishing"
    )
    sources: Dict[str, SourceMetadata] = Field(
        default_factory=dict,
        description="Mapping of stable source IDs to source metadata"
    )
    verification_result: Optional[VerificationReport] = Field(
        default=None,
        description="Result of citation and factual verification review"
    )
    verification_feedback: Optional[str] = Field(
        default=None,
        description="Feedback guidelines for article revision when verification fails"
    )
    revision_attempts: int = Field(
        default=0,
        description="Number of article revision attempts executed after verification failures"
    )
    final_article: Optional[str] = Field(
        default=None,
        description="Final article content after verification and publishing"
    )
    published_path: Optional[FilePath] = Field(
        default=None,
        description="Path to the article published"
    )
    photo_file_path: Optional[FilePath] = Field(
        default=None,
        description="Path to the photo generated by the photographer node"
    )
    photo_filename: Optional[str] = Field(
        default=None,
        description="Filename of the photo generated by the photographer node"
    )
    custom_event: Optional[HistoricalEvent] = Field(
        default=None,
        description="Custom event selected by the user for dispatch generation"
    )
    retriever: Optional[VectorStoreRetriever] = Field(
        default=None,
        description="Vector store for semantic search and retrieval"
    )
    retrieved_docs: List[Any] = Field(
        default_factory=list,
        description="Documents retrieved from vector store search node"
    )
    reranked_docs: List[Any] = Field(
        default_factory=list,
        description="Validated and re-ranked context documents"
    )
    error: StrictBool = Field(
        default=False,
        description="Whether or not to raise an error"
    )
    error_msg: Optional[str] = Field(
        default=None,
        description="Error message"
    )