"""
Main UI application for the Chrono S. Thompson application.
"""
import asyncio
import base64
from datetime import datetime
from pathlib import Path
import re
import time

import streamlit as st

from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent

# Page configuration for Streamlit
st.set_page_config(
    page_title="Chrono S. Thompson — Temporal Correspondent",
    page_icon="./avatar.svg",
    layout="wide"
)

OUTPUT_DIR = Path("storage/output")

def get_state() -> ChronoState:
    """Helper function to retrieve or initialize state in session state."""
    if "state" not in st.session_state:
        st.session_state.state = ChronoState()
    return st.session_state.state


def list_saved_dispatches():
    """Reads the output directory and returns a list of saved .md files sorted by modification time."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(list(OUTPUT_DIR.glob("*.md")), reverse=True)

def fetch_events_for_date(target_date: str):
    """Auxiliary function to fetch historical events for a specific date."""
    from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
    state = get_state()
    state.target_date = target_date
    return asyncio.run(fetch_events_node(state))

PIPELINE_NODES = [
    ("fetch_events", "1. Fetch Events", "🛰️"),
    ("batch_events", "2. Batch Events", "📦"),
    ("rank_events", "3. Rank Story", "🏆"),
    ("photographer", "4. Photographer", "🎨"),
    ("index_selected_event", "5. RAG Indexer", "📚"),
    ("search_context", "6. Vector Search", "🔎"),
    ("rerank_context", "7. Rerank Context", "📊"),
    ("write_article", "8. Gonzo Writer", "✍️"),
    ("verify_article", "9. Fact Verifier", "🔍"),
    ("publish_article", "10. Publisher", "💾"),
]

def render_pipeline_cards(statuses: dict[str, str], durations: dict[str, float] | None = None) -> str:
    """Renders a responsive visual stepper representing pipeline nodes with execution timers."""
    status_configs = {
        "pending": {
            "border": "rgba(150, 150, 150, 0.3)",
            "bg": "rgba(120, 120, 120, 0.08)",
            "color": "#888",
            "icon": "⏸️",
            "status_text": "Pending",
        },
        "running": {
            "border": "#38bdf8",
            "bg": "rgba(56, 189, 248, 0.15)",
            "color": "#38bdf8",
            "icon": "⏳",
            "status_text": "Running...",
        },
        "success": {
            "border": "#22c55e",
            "bg": "rgba(34, 197, 94, 0.15)",
            "color": "#22c55e",
            "icon": "✅",
            "status_text": "Completed",
        },
        "error": {
            "border": "#ef4444",
            "bg": "rgba(239, 68, 68, 0.15)",
            "color": "#ef4444",
            "icon": "❌",
            "status_text": "Error",
        },
        "skipped": {
            "border": "rgba(150, 150, 150, 0.3)",
            "bg": "rgba(80, 80, 80, 0.05)",
            "color": "#777",
            "icon": "⏭️",
            "status_text": "Skipped",
        },
    }

    cards_html = []
    for node_id, label, icon in PIPELINE_NODES:
        st_val = statuses.get(node_id, "pending")
        cfg = status_configs.get(st_val, status_configs["pending"])
        duration_badge = ""
        if durations and node_id in durations:
            duration_badge = f"⏱️ {durations[node_id]:.2f}s"
        elif st_val == "running":
            duration_badge = "⏱️ in progress"

        card = (
            f'<div style="background:{cfg["bg"]};border:1px solid {cfg["border"]};'
            f'border-radius:8px;padding:8px 10px;margin:3px;min-width:130px;'
            f'flex:1 1 calc(20% - 10px);box-sizing:border-box;'
            f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px;">'
            f'<span style="font-size:15px;">{icon}</span>'
            f'<span style="font-size:13px;">{cfg["icon"]}</span>'
            f'</div>'
            f'<div style="font-weight:600;font-size:12px;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
            f'{label}'
            f'</div>'
            f'<div style="display:flex;align-items:center;justify-content:space-between;font-size:10px;margin-top:3px;">'
            f'<span style="color:{cfg["color"]};font-weight:500;">{cfg["status_text"]}</span>'
            f'<span style="color:#94a3b8;font-size:9.5px;">{duration_badge}</span>'
            f'</div>'
            f'</div>'
        )
        cards_html.append(card)

    return (
        '<div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0 12px 0;'
        'background:rgba(15,23,42,0.35);padding:10px;border-radius:10px;'
        'border:1px solid rgba(255,255,255,0.08);">'
        + "".join(cards_html)
        + '</div>'
    )

def generate_mermaid_graph(statuses: dict[str, str], durations: dict[str, float] | None = None) -> str:
    """Generates a Mermaid graph string with dynamic node status markers and timers."""
    status_icons = {
        "pending": "⏸️",
        "running": "⏳",
        "success": "✅",
        "error": "❌",
        "skipped": "⏭️",
    }
    lines = [
        "```mermaid",
        "graph LR",
        '    classDef pending fill:#1e293b,stroke:#475569,stroke-width:1px,color:#94a3b8;',
        '    classDef running fill:#075985,stroke:#38bdf8,stroke-width:2px,color:#ffffff;',
        '    classDef success fill:#064e3b,stroke:#22c55e,stroke-width:2px,color:#ffffff;',
        '    classDef error fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#ffffff;',
        '    classDef skipped fill:#1e1e24,stroke:#475569,stroke-dasharray: 4 4,color:#64748b;',
    ]
    for node_id, label, icon in PIPELINE_NODES:
        st_val = statuses.get(node_id, "pending")
        sym = status_icons.get(st_val, "⏸️")
        time_suffix = f" ({durations[node_id]:.1f}s)" if durations and node_id in durations else ""
        lines.append(f'    {node_id}["{icon} {label} {sym}{time_suffix}"]:::{st_val}')

    lines.extend([
        "    fetch_events --> batch_events --> rank_events --> photographer --> index_selected_event --> search_context",
        "    search_context --> rerank_context --> write_article --> verify_article --> publish_article",
        "    search_context -.->|if 0 docs| write_article",
        "    verify_article -.->|revision| write_article",
        "```",
    ])
    return "\n".join(lines)

async def stream_pipeline_execution(
    initial_state: ChronoState,
    progress_bar,
    graph_placeholder,
    mermaid_placeholder,
    log_placeholder,
):
    """Executes the LangGraph pipeline via astream, updating UI placeholders in real time."""
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    app = build_chrono_graph()

    statuses = {node_id: "pending" for node_id, _, _ in PIPELINE_NODES}
    statuses["fetch_events"] = "running"
    node_start_times: dict[str, float] = {"fetch_events": time.perf_counter()}
    node_durations: dict[str, float] = {}
    logs = []
    has_error = False
    error_msg = ""

    def update_progress():
        if progress_bar is None:
            return
        completed = sum(1 for nid, _, _ in PIPELINE_NODES if statuses.get(nid) in ("success", "skipped"))
        running = sum(0.5 for nid, _, _ in PIPELINE_NODES if statuses.get(nid) == "running")
        progress_val = min(1.0, (completed + running) / len(PIPELINE_NODES))
        pct = int(progress_val * 100)
        total_time = sum(node_durations.values())
        if has_error:
            progress_bar.progress(progress_val, text=f"⚠️ Execution failure ({pct}%)")
        elif completed == len(PIPELINE_NODES):
            progress_bar.progress(1.0, text=f"✅ Pipeline completed successfully in {total_time:.2f}s! (100%)")
        else:
            current_running = [label for nid, label, _ in PIPELINE_NODES if statuses.get(nid) == "running"]
            current_text = current_running[0] if current_running else "In progress"
            progress_bar.progress(progress_val, text=f"Progress: {pct}% — {current_text}")

    def refresh_ui(msg: str | None = None):
        if msg:
            logs.append(msg)
        update_progress()
        card_html = render_pipeline_cards(statuses, node_durations)
        if hasattr(graph_placeholder, "html"):
            graph_placeholder.html(card_html)
        else:
            graph_placeholder.markdown(card_html, unsafe_allow_html=True)
        if mermaid_placeholder is not None:
            mermaid_placeholder.markdown(generate_mermaid_graph(statuses, node_durations))
        if logs and log_placeholder is not None:
            log_placeholder.markdown("\n".join(f"- {l}" for l in logs))

    refresh_ui("🚀 **Starting pipeline**: Connecting to temporal vortex...")

    accumulated_state = initial_state.model_dump()

    try:
        async for chunk in app.astream(initial_state):
            for node_name, node_update in chunk.items():
                if isinstance(node_update, dict):
                    accumulated_state.update(node_update)

                elapsed = time.perf_counter() - node_start_times.get(node_name, time.perf_counter())
                node_durations[node_name] = elapsed

                if isinstance(node_update, dict) and node_update.get("error"):
                    statuses[node_name] = "error"
                    has_error = True
                    error_msg = node_update.get("error_msg", f"Error in node {node_name}")
                    refresh_ui(f"❌ **{node_name}** ({elapsed:.2f}s): {error_msg}")
                    break

                statuses[node_name] = "success"

                msg = None
                if node_name == "fetch_events":
                    evts = node_update.get("raw_events", [])
                    msg = f"🛰️ **Fetch Events** ({elapsed:.2f}s): {len(evts)} historical events retrieved via FastMCP"
                    statuses["batch_events"] = "running"
                    node_start_times["batch_events"] = time.perf_counter()
                elif node_name == "batch_events":
                    b = node_update.get("batched_events")
                    count = len(b.events) if b and hasattr(b, "events") else 0
                    msg = f"📦 **Batch Events** ({elapsed:.2f}s): {count} candidate events structured by relevance"
                    statuses["rank_events"] = "running"
                    node_start_times["rank_events"] = time.perf_counter()
                elif node_name == "rank_events":
                    curated = node_update.get("curated_story")
                    if curated and hasattr(curated, "selected_event"):
                        msg = f"🏆 **Rank Story** ({elapsed:.2f}s): [{curated.selected_event.year}] {curated.selected_event.title[:50]}... | Gonzo editorial hook established"
                    else:
                        msg = f"🏆 **Rank Story** ({elapsed:.2f}s): Editorial curated with high narrative tension"
                    statuses["photographer"] = "running"
                    node_start_times["photographer"] = time.perf_counter()
                elif node_name == "photographer":
                    fname = node_update.get("photo_filename") or "illustration.png"
                    msg = f"🎨 **Photographer** ({elapsed:.2f}s): Historical illustration synthesized (`{fname}`)"
                    statuses["index_selected_event"] = "running"
                    node_start_times["index_selected_event"] = time.perf_counter()
                elif node_name == "index_selected_event":
                    msg = f"📚 **RAG Indexer** ({elapsed:.2f}s): Cleaned Wikipedia article indexed in memory vector store"
                    statuses["search_context"] = "running"
                    node_start_times["search_context"] = time.perf_counter()
                elif node_name == "search_context":
                    docs = node_update.get("retrieved_docs", [])
                    msg = f"🔎 **Vector Search** ({elapsed:.2f}s): {len(docs)} contextual chunks retrieved"
                    if len(docs) < 1:
                        statuses["rerank_context"] = "skipped"
                        statuses["write_article"] = "running"
                        node_start_times["write_article"] = time.perf_counter()
                    else:
                        statuses["rerank_context"] = "running"
                        node_start_times["rerank_context"] = time.perf_counter()
                elif node_name == "rerank_context":
                    srcs = node_update.get("sources", {})
                    src_keys = list(srcs.keys()) if isinstance(srcs, dict) else []
                    msg = f"📊 **Rerank Context** ({elapsed:.2f}s): Passages deduplicated and sources mapped ({', '.join(src_keys)})"
                    statuses["write_article"] = "running"
                    node_start_times["write_article"] = time.perf_counter()
                elif node_name == "write_article":
                    draft = node_update.get("draft_article", "")
                    msg = f"✍️ **Gonzo Writer** ({elapsed:.2f}s): Dispatch drafted with {len(draft)} characters and inline citations"
                    statuses["verify_article"] = "running"
                    node_start_times["verify_article"] = time.perf_counter()
                elif node_name == "verify_article":
                    vr = node_update.get("verification_result")
                    if vr and getattr(vr, "is_valid", False):
                        msg = f"🔍 **Fact Verifier** ({elapsed:.2f}s): Dispatch successfully approved across citation and factual audit"
                        statuses["publish_article"] = "running"
                        node_start_times["publish_article"] = time.perf_counter()
                    else:
                        attempts = node_update.get("revision_attempts", 1)
                        msg = f"🔄 **Fact Verifier** ({elapsed:.2f}s): Feedback issued, rerouting for revision (attempt {attempts})"
                        statuses["write_article"] = "running"
                        node_start_times["write_article"] = time.perf_counter()
                elif node_name == "publish_article":
                    path = node_update.get("published_path", "")
                    msg = f"💾 **Publisher** ({elapsed:.2f}s): Dispatch finalized and saved to `{path}`"

                refresh_ui(msg)

            if has_error:
                break

    except Exception as exc:
        has_error = True
        error_msg = str(exc)
        for nid, st_val in statuses.items():
            if st_val == "running":
                statuses[nid] = "error"
        refresh_ui(f"❌ **Execution failure**: {error_msg}")

    if not has_error and progress_bar is not None:
        total_time = sum(node_durations.values())
        progress_bar.progress(1.0, text=f"✅ Pipeline completed successfully in {total_time:.2f}s! (100%)")

    return accumulated_state, has_error, error_msg, statuses, logs, node_durations

# --- State Initialization & Execution Status ---
saved_files = list_saved_dispatches()

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "view_archive" if saved_files else "idle"
if "custom_events" not in st.session_state:
    st.session_state.custom_events = None
if "selected_custom_event" not in st.session_state:
    st.session_state.selected_custom_event = None
if "active_article" not in st.session_state:
    st.session_state.active_article = None
if "execution_done" not in st.session_state:
    st.session_state.execution_done = False
if "execution_result" not in st.session_state:
    st.session_state.execution_result = None
if "final_statuses" not in st.session_state:
    st.session_state.final_statuses = None
if "final_logs" not in st.session_state:
    st.session_state.final_logs = None
if "final_durations" not in st.session_state:
    st.session_state.final_durations = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "should_scroll_top" not in st.session_state:
    st.session_state.should_scroll_top = False

# Compute whether a pipeline execution is actively running
is_running = (
    st.session_state.get("is_running", False)
    or (st.session_state.get("view_mode") == "generate_random" and not st.session_state.get("execution_done", False))
    or (st.session_state.get("view_mode") == "select_event" and st.session_state.get("selected_custom_event") is not None and not st.session_state.get("execution_done", False))
)

def scroll_to_top():
    """Scrolls the page viewport smoothly to the top."""
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        setTimeout(function() {
            try {
                var doc = window.parent.document;
                var anchor = doc.getElementById('top-anchor');
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                var main = doc.querySelector('section.main') || doc.querySelector('[data-testid="stMain"]') || doc.querySelector('.main');
                if (main) {
                    main.scrollTo({ top: 0, behavior: 'smooth' });
                }
                window.parent.scrollTo({ top: 0, behavior: 'smooth' });
            } catch(e) {
                window.parent.scrollTo(0, 0);
            }
        }, 80);
        </script>
        """,
        height=0,
        width=0,
    )

# --- Generates the sidebar ---
with st.sidebar:
    st.header("⚙️ Control Panel")

    input_date = st.text_input(
        "Target Date (MM/DD):",
        value=datetime.now().strftime("%m/%d"),
        help="Enter the month and day for temporal coverage.",
        disabled=is_running,
    )

    generate_btn = st.button(
        "🚀 Random Dispatch",
        use_container_width=True,
        help="Generate a random dispatch for the selected date.",
        disabled=is_running,
    )
    custom_event_btn = st.button(
        "📅 Select Event",
        use_container_width=True,
        help="Generate a dispatch based on a selected historical event for the selected date.",
        disabled=is_running,
    )

    st.divider()
    st.subheader("📁 Newsroom Archives")

    selected_file = None
    if saved_files:
        options = {f.name: f for f in saved_files}
        choice = st.selectbox(
            "Select a past edition:",
            list(options.keys()),
            key="archive_selectbox",
            disabled=is_running,
        )
        selected_file = options[choice]
        if "last_selected_file" not in st.session_state:
            st.session_state.last_selected_file = choice
        elif st.session_state.last_selected_file != choice:
            st.session_state.last_selected_file = choice
            st.session_state.view_mode = "view_archive"
    else:
        st.caption("No archived dispatches.")


# --- Main Area ---
st.html('<div id="top-anchor"></div>')

if st.session_state.get("should_scroll_top", False):
    scroll_to_top()
    st.session_state.should_scroll_top = False

col1, col2 = st.columns([0.08, 0.92])
with col1:
    st.image("./avatar.svg", width=120)

with col2:
    st.title("Chrono S. Thompson: The Gonzo Gazette")
    st.caption("Autonomous temporal correspondent across eras.")

def resolve_image_path(img_path_str: str) -> Path | None:
    """Tries multiple candidate locations to locate an image file on disk."""
    raw_path = Path(img_path_str.strip().replace("\\", "/"))

    # 1. Direct path check (e.g., relative to working directory)
    if raw_path.exists() and raw_path.is_file():
        return raw_path

    # 2. Relative to storage/output/
    output_relative = (Path("storage/output") / raw_path).resolve()
    if output_relative.exists() and output_relative.is_file():
        return output_relative

    # 3. Direct filename lookup inside storage/images/
    images_dir_file = Path("storage/images") / raw_path.name
    if images_dir_file.exists() and images_dir_file.is_file():
        return images_dir_file

    return None

def process_markdown_images(content: str) -> str:
    """Converts local image file paths in HTML <img> tags or markdown syntax to base64 Data URIs for Streamlit rendering."""
    if not content:
        return content

    def replace_html_src(match):
        prefix, img_path, suffix = match.group(1), match.group(2), match.group(3)
        found_path = resolve_image_path(img_path)
        if found_path:
            mime_type = "image/png" if found_path.suffix.lower() == ".png" else "image/jpeg"
            encoded = base64.b64encode(found_path.read_bytes()).decode("utf-8")
            data_uri = f"data:{mime_type};base64,{encoded}"
            return f'{prefix}{data_uri}{suffix}'
        return match.group(0)

    html_pattern = r'(<img\s+[^>]*src=["\'])([^"\']+)(["\'][^>]*>)'
    content = re.sub(html_pattern, replace_html_src, content, flags=re.IGNORECASE)

    def replace_md_src(match):
        alt, img_path = match.group(1), match.group(2)
        found_path = resolve_image_path(img_path)
        if found_path:
            mime_type = "image/png" if found_path.suffix.lower() == ".png" else "image/jpeg"
            encoded = base64.b64encode(found_path.read_bytes()).decode("utf-8")
            data_uri = f"data:{mime_type};base64,{encoded}"
            return f'![{alt}]({data_uri})'
        return match.group(0)

    md_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    content = re.sub(md_pattern, replace_md_src, content)

    return content

def render_article_with_translation(content: str, key_id: str = "article"):
    """Renders the article markdown with a button to translate it to Portuguese using Hugging Face transformers pipeline."""
    if not content:
        st.error("Empty article.")
        return

    processed_content = process_markdown_images(content)

    col_space, col_btn = st.columns([0.65, 0.35])
    with col_btn:
        if st.button("🌐 Translate to Portuguese (Transformers)", key=f"btn_translate_{key_id}", disabled=is_running):
            with st.spinner("Translating article via Hugging Face transformers pipeline (Helsinki-NLP/opus-mt-tc-big-en-pt)..."):
                from src.chrono_s_thompson.core.translator import translate_markdown_text
                st.session_state[f"trans_cache_{key_id}"] = translate_markdown_text(content)

    translated_content = st.session_state.get(f"trans_cache_{key_id}")
    if translated_content:
        processed_translated = process_markdown_images(translated_content)
        tab_en, tab_pt = st.tabs(["🇺🇸 English (Original)", "🇧🇷 Portuguese"])
        with tab_en:
            st.markdown(processed_content, unsafe_allow_html=True)
        with tab_pt:
            st.markdown(processed_translated, unsafe_allow_html=True)
    else:
        st.markdown(processed_content, unsafe_allow_html=True)

if generate_btn:
    st.session_state.view_mode = "generate_random"
    st.session_state.custom_events = None
    st.session_state.selected_custom_event = None
    st.session_state.execution_done = False
    st.session_state.execution_result = None
    st.session_state.final_statuses = None
    st.session_state.final_logs = None
    st.session_state.final_durations = None
    st.session_state.should_scroll_top = True

elif custom_event_btn:
    if type(input_date) != str or len(input_date.strip()) != 5 or input_date[2] != '/':
        st.error("Please provide a target date in MM/DD format before selecting an event.")
    else:
        with st.spinner(f"Querying historical events for {input_date}..."):
            fetch_result = fetch_events_for_date(input_date)
            raw_evts = fetch_result.get('raw_events', [])
            events_list = [
                e if isinstance(e, HistoricalEvent) else HistoricalEvent(**e)
                for e in raw_evts
            ]
            st.session_state.custom_events = events_list
            st.session_state.selected_custom_event = None
            st.session_state.execution_done = False
            st.session_state.execution_result = None
            st.session_state.final_statuses = None
            st.session_state.final_logs = None
            st.session_state.final_durations = None
            st.session_state.should_scroll_top = True
            st.session_state.view_mode = "select_event"

# Trigger main area render based on view_mode
if st.session_state.view_mode == "generate_random":
    if not input_date or len(input_date.strip()) != 5 or input_date[2] != '/':
        st.error("Please provide a target date in MM/DD format before generating a dispatch.")
        st.session_state.view_mode = "idle"
    else:
        # Alert container positioned at the top of the page
        alert_placeholder = st.container()

        st.markdown("### 🧭 Graph Execution Tracker")
        progress_bar = st.progress(0.0, text="Initializing temporal pipeline...")
        graph_placeholder = st.empty()
        with st.expander("🗺️ Mermaid Flow Diagram", expanded=False):
            mermaid_placeholder = st.empty()
        st.markdown("#### 📜 Activity Log & State Mutations:")
        log_placeholder = st.empty()

        if not st.session_state.get("execution_done", False):
            with st.status(f"⚡ Connecting to temporal vortex for {input_date}...", expanded=True) as status:
                state = ChronoState(target_date=input_date)
                st.session_state.is_running = True
                try:
                    result, has_error, err_msg, final_statuses, final_logs, final_durations = asyncio.run(
                        stream_pipeline_execution(
                            state,
                            progress_bar,
                            graph_placeholder,
                            mermaid_placeholder,
                            log_placeholder,
                        )
                    )
                finally:
                    st.session_state.is_running = False

                st.session_state.execution_done = True
                st.session_state.execution_result = result
                st.session_state.has_error = has_error
                st.session_state.err_msg = err_msg
                st.session_state.final_statuses = final_statuses
                st.session_state.final_logs = final_logs
                st.session_state.final_durations = final_durations

                if not has_error and result.get("final_article"):
                    status.update(label="✨ Dispatch completed successfully!", state="complete", expanded=False)
                    scroll_to_top()
                else:
                    status.update(label="Temporal coverage failure!", state="error")
        else:
            statuses = st.session_state.get("final_statuses", {})
            logs = st.session_state.get("final_logs", [])
            durations = st.session_state.get("final_durations", {})
            has_error = st.session_state.get("has_error", False)
            card_html = render_pipeline_cards(statuses, durations)
            if hasattr(graph_placeholder, "html"):
                graph_placeholder.html(card_html)
            else:
                graph_placeholder.markdown(card_html, unsafe_allow_html=True)
            if mermaid_placeholder is not None:
                mermaid_placeholder.markdown(generate_mermaid_graph(statuses, durations))
            if logs and log_placeholder is not None:
                log_placeholder.markdown("\n".join(f"- {l}" for l in logs))
            total_time = sum(durations.values()) if durations else 0.0
            if not has_error:
                progress_bar.progress(1.0, text=f"✅ Pipeline completed successfully in {total_time:.2f}s! (100%)")
            else:
                progress_bar.progress(1.0, text="⚠️ Execution failure")

        result = st.session_state.get("execution_result", {})
        has_error = st.session_state.get("has_error", False)
        err_msg = st.session_state.get("err_msg", "")

        if not has_error and result.get("final_article"):
            with alert_placeholder:
                st.success("🎉 **Generation completed successfully!** The temporal dispatch has been drafted, verified, and saved to archives.")
                col_info, col_btn = st.columns([0.65, 0.35])
                with col_info:
                    st.info("Would you like to view the article now?")
                with col_btn:
                    if st.button("📰 View Article", type="primary", use_container_width=True, key="btn_view_random_article"):
                        st.session_state.active_article = {
                            "content": result.get("final_article", ""),
                            "published_path": result.get("published_path", ""),
                            "key_id": "generated_random"
                        }
                        st.session_state.view_mode = "show_article"
                        st.session_state.should_scroll_top = True
                        st.rerun()
                st.divider()
        elif has_error:
            with alert_placeholder:
                st.error(f"❌ Error executing pipeline: {err_msg}")

elif st.session_state.view_mode == "select_event" and st.session_state.custom_events:
    selected_event = st.session_state.get("selected_custom_event")

    if selected_event is None:
        st.subheader(f"📅 Historical Events for {input_date}")
        st.write("Select an event to generate a dedicated Gonzo dispatch:")
        for idx, event in enumerate(st.session_state.custom_events):
            col_info, col_btn = st.columns([0.75, 0.25])
            with col_info:
                st.markdown(f"- **{event.year}**: {event.title}")
            with col_btn:
                safe_key = f"btn_event_{event.year}_{idx}"
                if st.button("🚀 Generate Dispatch", key=safe_key, use_container_width=True, disabled=is_running):
                    st.session_state.selected_custom_event = event
                    st.session_state.execution_done = False
                    st.session_state.execution_result = None
                    st.session_state.final_statuses = None
                    st.session_state.final_logs = None
                    st.session_state.final_durations = None
                    st.session_state.should_scroll_top = True
                    st.rerun()
    else:
        # Alert container positioned at the top of the page
        alert_placeholder = st.container()

        # A custom event has been selected -> remove all other event buttons!
        col_hdr, col_back = st.columns([0.75, 0.25])
        with col_hdr:
            st.subheader(f"🎯 Selected Event: [{selected_event.year}] {selected_event.title}")
        with col_back:
            if st.button("⬅️ Select Another Event", use_container_width=True, disabled=is_running):
                st.session_state.selected_custom_event = None
                st.session_state.execution_done = False
                st.session_state.execution_result = None
                st.session_state.final_statuses = None
                st.session_state.final_logs = None
                st.session_state.final_durations = None
                st.session_state.should_scroll_top = True
                st.rerun()

        st.markdown("### 🧭 Graph Execution Tracker")
        progress_bar = st.progress(0.0, text="Initializing temporal pipeline...")
        graph_placeholder = st.empty()
        with st.expander("🗺️ Mermaid Flow Diagram", expanded=False):
            mermaid_placeholder = st.empty()
        st.markdown("#### 📜 Activity Log & State Mutations:")
        log_placeholder = st.empty()

        if not st.session_state.get("execution_done", False):
            with st.status(f"⚡ Connecting to temporal vortex for [{selected_event.year}] {selected_event.title}...", expanded=True) as status:
                state = ChronoState(target_date=input_date, custom_event=selected_event)
                st.session_state.is_running = True
                try:
                    result, has_error, err_msg, final_statuses, final_logs, final_durations = asyncio.run(
                        stream_pipeline_execution(
                            state,
                            progress_bar,
                            graph_placeholder,
                            mermaid_placeholder,
                            log_placeholder,
                        )
                    )
                finally:
                    st.session_state.is_running = False

                st.session_state.execution_done = True
                st.session_state.execution_result = result
                st.session_state.has_error = has_error
                st.session_state.err_msg = err_msg
                st.session_state.final_statuses = final_statuses
                st.session_state.final_logs = final_logs
                st.session_state.final_durations = final_durations

                if not has_error and result.get("final_article"):
                    status.update(label="✨ Dispatch completed successfully!", state="complete", expanded=False)
                    scroll_to_top()
                else:
                    status.update(label="Temporal coverage failure!", state="error")
        else:
            statuses = st.session_state.get("final_statuses", {})
            logs = st.session_state.get("final_logs", [])
            durations = st.session_state.get("final_durations", {})
            has_error = st.session_state.get("has_error", False)
            card_html = render_pipeline_cards(statuses, durations)
            if hasattr(graph_placeholder, "html"):
                graph_placeholder.html(card_html)
            else:
                graph_placeholder.markdown(card_html, unsafe_allow_html=True)
            if mermaid_placeholder is not None:
                mermaid_placeholder.markdown(generate_mermaid_graph(statuses, durations))
            if logs and log_placeholder is not None:
                log_placeholder.markdown("\n".join(f"- {l}" for l in logs))
            total_time = sum(durations.values()) if durations else 0.0
            if not has_error:
                progress_bar.progress(1.0, text=f"✅ Pipeline completed successfully in {total_time:.2f}s! (100%)")
            else:
                progress_bar.progress(1.0, text="⚠️ Execution failure")

        result = st.session_state.get("execution_result", {})
        has_error = st.session_state.get("has_error", False)
        err_msg = st.session_state.get("err_msg", "")

        if not has_error and result.get("final_article"):
            with alert_placeholder:
                st.success("🎉 **Generation completed successfully!** The temporal dispatch has been drafted, verified, and saved to archives.")
                col_info, col_btn = st.columns([0.65, 0.35])
                with col_info:
                    st.info("Would you like to view the article now?")
                with col_btn:
                    if st.button("📰 View Article", type="primary", use_container_width=True, key="btn_view_custom_article"):
                        st.session_state.active_article = {
                            "content": result.get("final_article", ""),
                            "published_path": result.get("published_path", ""),
                            "key_id": f"generated_custom_{selected_event.year}"
                        }
                        st.session_state.custom_events = None
                        st.session_state.selected_custom_event = None
                        st.session_state.view_mode = "show_article"
                        st.session_state.should_scroll_top = True
                        st.rerun()
                st.divider()
        elif has_error:
            with alert_placeholder:
                st.error(f"❌ Error executing pipeline: {err_msg}")

elif st.session_state.view_mode == "show_article" and st.session_state.active_article:
    article_data = st.session_state.active_article
    if article_data.get("published_path"):
        st.success(f"Article published to: `{article_data.get('published_path')}`")
    render_article_with_translation(article_data.get("content", ""), key_id=article_data.get("key_id", "article"))

elif selected_file:
    st.subheader(f"Edition: {selected_file.stem}")
    content = selected_file.read_text(encoding="utf-8")
    render_article_with_translation(content, key_id=selected_file.stem)

else:
    st.info("Select a past edition from the sidebar or click **Random Dispatch** or **Select Event** to start.")

