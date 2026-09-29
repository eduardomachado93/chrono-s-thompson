"""
Node responsible for factual verification and citation auditing in the Chrono S. Thompson LangGraph workflow.
"""
import logging
import re
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import (
    ChronoState,
    ClaimVerification,
    VerificationReport,
)
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import VERIFIER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MAX_REVISION_ATTEMPTS = 2

verifier_prompt = ChatPromptTemplate.from_messages([
    ("system", VERIFIER_SYSTEM_PROMPT),
    ("user", """ARTICLE DRAFT TO VERIFY:
{draft_article}

AVAILABLE SOURCES:
{sources_context}

Analyze the factual claims and citation IDs. Verify if all citations exist in the sources and whether claims are supported.""")
])

async def verify_article_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for fact-checking and auditing citations of the generated draft.

    Args:
        state: The current state of the pipeline containing `draft_article`, `sources`, and `revision_attempts`.

    Returns:
        State mutation dictionary with `verification_result`, `verification_feedback`, and `revision_attempts`, or an error payload.
    """
    draft_article = state.draft_article
    sources = state.sources or {}

    if not draft_article:
        return {"error": True, "error_msg": "[Node: verify_article] Draft article not found in state."}

    logger.info("[Node: verify_article] Performing citation check and factual verification...")

    # 1. Deterministic Citation & Structure Check
    parts = re.split(r'###\s*(?:Sources|Sources)', draft_article, maxsplit=1, flags=re.IGNORECASE)
    body_text = parts[0]
    has_sources_section = len(parts) > 1

    # Extract inline citations strictly from the body text before sources section
    body_cited_ids = sorted(list(set(re.findall(r'\[(S\d+)\]', body_text))))
    has_inline_citations = len(body_cited_ids) > 0

    # Extract all cited IDs across the draft to detect invalid/nonexistent source IDs
    all_cited_ids = sorted(list(set(re.findall(r'\[(S\d+)\]', draft_article))))
    valid_source_ids = set(sources.keys())
    missing_ids = [cid for cid in all_cited_ids if cid not in valid_source_ids]

    def normalize_ws(text: str) -> str:
        return " ".join(text.split()) if text else ""

    def clean_text_for_matching(text: str) -> str:
        if not text:
            return ""
        return re.sub(r'[\W_]+', '', text).lower()

    def check_evidence_match(evidence: str, source_content: str) -> bool:
        if not evidence or not source_content:
            return False
        source_clean = clean_text_for_matching(source_content)
        evidence_clean = clean_text_for_matching(evidence)
        if evidence_clean in source_clean:
            return True
        # Check keyword overlap ratio (handles slight LLM paraphrasing/summary in evidence field)
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{4,}\b', evidence)]
        if not words:
            return True
        hits = sum(1 for w in words if w in source_clean)
        return (hits / len(words)) >= 0.4

    feedback_parts: List[str] = []
    if not has_sources_section:
        feedback_parts.append("Missing required '### Sources' section at the end of the article.")
    if not has_inline_citations:
        feedback_parts.append("Missing inline citations in the body text (e.g. [S1], [S2]).")
    if missing_ids:
        feedback_parts.append(f"Invalid citation IDs used in text: {missing_ids}. Only use valid IDs: {sorted(list(valid_source_ids))}.")

    initial_structural_valid = has_sources_section and has_inline_citations and (len(missing_ids) == 0)

    # Prepare context for LLM verification
    sources_context_lines = []
    for sid, s_meta in sources.items():
        sources_context_lines.append(f"[{sid}] Title: {s_meta.title} | URL: {s_meta.url}\nExcerpt: {s_meta.content}")
    sources_context = "\n\n".join(sources_context_lines) if sources_context_lines else "No sources provided."

    llm = ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        temperature=0.0
    ).with_structured_output(VerificationReport)

    chain = verifier_prompt | llm

    try:
        llm_report: VerificationReport = await chain.ainvoke({
            "draft_article": draft_article,
            "sources_context": sources_context,
        })
        
        claims = llm_report.claims or []
        claims_valid = True

        if not claims:
            feedback_parts.append("Verification report contains no claims to verify.")
            claims_valid = False
        else:
            for claim in claims:
                # Ignore meta-verification summary items inserted by the verifier LLM
                claim_text_lower = claim.claim.lower()
                if any(k in claim_text_lower for k in ["cited id", "source map", "### source", "sources section", "structural check"]):
                    logger.info(f"[Node: verify_article] Skipping meta-verification item in claims list: '{claim.claim}'")
                    continue

                # Auto-heal missing or None source_id if evidence snippet or claim text matches content in any valid source
                if (not claim.source_id or claim.source_id.strip().lower() in ("", "none")):
                    match_target = claim.evidence if claim.evidence and claim.evidence.strip() else claim.claim
                    target_clean = clean_text_for_matching(match_target)
                    if target_clean:
                        for sid, s_meta in sources.items():
                            if target_clean in clean_text_for_matching(s_meta.content):
                                claim.source_id = sid
                                claim.status = "supported"
                                if not claim.evidence:
                                    claim.evidence = match_target
                                break

                # 1. Status must be "supported"
                if claim.status != "supported":
                    feedback_parts.append(f"Claim '{claim.claim}' has unsupported status '{claim.status}'.")
                    claims_valid = False

                # 2. source_id must exist in state.sources
                if not claim.source_id or claim.source_id not in valid_source_ids:
                    feedback_parts.append(f"Claim '{claim.claim}' references missing or invalid source_id '{claim.source_id}'.")
                    claims_valid = False
                elif claim.source_id not in body_cited_ids:
                    # 3. source_id must be cited inline in the body text
                    feedback_parts.append(f"Claim '{claim.claim}' references source_id '{claim.source_id}' which is not cited inline in the body text.")
                    claims_valid = False

                # 4. evidence snippet must exist and match source content
                if not claim.evidence or not claim.evidence.strip():
                    feedback_parts.append(f"Claim '{claim.claim}' lacks supporting evidence snippet.")
                    claims_valid = False
                elif claim.source_id in valid_source_ids:
                    if not check_evidence_match(claim.evidence, sources[claim.source_id].content):
                        feedback_parts.append(f"Evidence snippet for claim '{claim.claim}' was not found in source [{claim.source_id}].")
                        claims_valid = False

        # Deterministic checks MUST take precedence over LLM report is_valid flag
        is_valid = initial_structural_valid and claims_valid and llm_report.is_valid
        
        feedback_str = " | ".join(feedback_parts) if feedback_parts else llm_report.feedback

        final_report = VerificationReport(
            is_valid=is_valid,
            cited_ids=body_cited_ids,
            missing_citation_ids=missing_ids,
            claims=llm_report.claims,
            feedback=feedback_str,
            limitation_notice="Automated LLM fact-checking is a heuristic verification layer and does not guarantee absolute historical truth."
        )

        current_attempts = state.revision_attempts

        if not is_valid:
            if current_attempts >= MAX_REVISION_ATTEMPTS:
                error_msg = f"[Node: verify_article] Fact verification failed after maximum attempts ({MAX_REVISION_ATTEMPTS}). Feedback: {feedback_str}"
                logger.warning(error_msg)
                return {
                    "error": True,
                    "error_msg": error_msg,
                    "verification_result": final_report,
                }
            
            logger.info(f"[Node: verify_article] Verification failed (attempt {current_attempts + 1}/{MAX_REVISION_ATTEMPTS}). Triggering revision with feedback.")
            return {
                "verification_result": final_report,
                "verification_feedback": feedback_str,
                "revision_attempts": current_attempts + 1,
            }

        logger.info("[Node: verify_article] Fact verification passed successfully!")
        return {
            "verification_result": final_report,
            "verification_feedback": None,
        }

    except Exception as exc:
        # Sanitize exception message before logging to avoid exposing sensitive keys in logs
        exc_str = str(exc)
        sanitized_exc = re.sub(r'sk-[A-Za-z0-9T3BlbkFJ\-_]{20,}', '[REDACTED]', exc_str)
        logger.error(f"[Node: verify_article] Fact verification service failed: {sanitized_exc}")
        
        fallback_report = VerificationReport(
            is_valid=False,
            cited_ids=body_cited_ids,
            missing_citation_ids=missing_ids,
            claims=[],
            feedback=f"Verification service error: {sanitized_exc}",
            limitation_notice="Automated LLM fact-checking is a heuristic verification layer and does not guarantee absolute historical truth."
        )

        # Verification service failure blocks publication without triggering content revision loops
        return {
            "error": True,
            "error_msg": f"[Node: verify_article] Fact verification service failed: {sanitized_exc}",
            "verification_result": fallback_report,
            "verification_feedback": None,
        }
