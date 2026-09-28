import asyncio
import base64
from datetime import datetime
from pathlib import Path
import re
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

async def run_pipeline():
    """Executes the full LangGraph pipeline for a given target date and returns the final state."""
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    state = get_state()
    state.custom_event = None
    app = build_chrono_graph()
    return await app.ainvoke(state)

async def run_pipeline_with_custom_event(custom_event: HistoricalEvent, date_str: str):
    """Executes the full LangGraph pipeline for a given target date and a custom historical event."""
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    state = get_state()
    state.custom_event = custom_event
    state.target_date = date_str
    app = build_chrono_graph()
    return await app.ainvoke(state)

# --- Generates the sidebar ---
with st.sidebar:
    st.header("⚙️ Control Panel")

    input_date = st.text_input(
        "Target Date (MM/DD):",
        value=datetime.now().strftime("%m/%d"),
        help="Enter the month and day for temporal coverage."
    )

    generate_btn = st.button("🚀 Random Dispatch", use_container_width=True, help="Generate a random dispatch for the selected date.")
    custom_event_btn = st.button("📅 Select Event", use_container_width=True, help="Generate a dispatch based on a selected historical event for the selected date.")

    st.divider()
    st.subheader("📁 Newsroom Archives")
    saved_files = list_saved_dispatches()

    selected_file = None
    if saved_files:
        options = {f.name: f for f in saved_files}
        choice = st.selectbox("Select a past edition:", list(options.keys()), key="archive_selectbox")
        selected_file = options[choice]
        if "last_selected_file" not in st.session_state:
            st.session_state.last_selected_file = choice
        elif st.session_state.last_selected_file != choice:
            st.session_state.last_selected_file = choice
            st.session_state.view_mode = "view_archive"
    else:
        st.caption("No archived dispatches.")


# --- Main Area ---
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

    col_space, col_btn = st.columns([0.7, 0.3])
    with col_btn:
        if st.button("🌐 Traduzir para PT (Transformers)", key=f"btn_translate_{key_id}"):
            with st.spinner("Traduzindo artigo via Hugging Face transformers pipeline (Helsinki-NLP/opus-mt-en-pt)..."):
                from src.chrono_s_thompson.core.translator import translate_markdown_text
                st.session_state[f"trans_cache_{key_id}"] = translate_markdown_text(content)

    translated_content = st.session_state.get(f"trans_cache_{key_id}")
    if translated_content:
        processed_translated = process_markdown_images(translated_content)
        tab_pt, tab_en = st.tabs(["🇧🇷 Português", "🇺🇸 English (Original)"])
        with tab_pt:
            st.markdown(processed_translated, unsafe_allow_html=True)
        with tab_en:
            st.markdown(processed_content, unsafe_allow_html=True)
    else:
        st.markdown(processed_content, unsafe_allow_html=True)

# State management for view mode, custom events list, and active generated article
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "view_archive" if saved_files else "idle"
if "custom_events" not in st.session_state:
    st.session_state.custom_events = None
if "active_article" not in st.session_state:
    st.session_state.active_article = None

if generate_btn:
    st.session_state.view_mode = "generate_random"
    st.session_state.custom_events = None

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
            st.session_state.view_mode = "select_event"

# Trigger main area render based on view_mode
if st.session_state.view_mode == "generate_random":
    with st.status(f"Connecting to temporal vortex for {input_date}...", expanded=True) as status:
        st.write("🧠 Curating story with maximum dramatic tension...")
        st.write("📰 Drafting dispatch in Gonzo style...")
        if input_date is None:
            status.update(label="Temporal coverage failure!", state="error")
            st.error(f"Input Date not Found")
        else:
            try:
                state = get_state()
                state.target_date = input_date
                result = asyncio.run(run_pipeline())
                status.update(label="Dispatch complete!", state="complete", expanded=False)
                st.session_state.active_article = {
                    "content": result.get("final_article", ""),
                    "published_path": result.get("published_path", ""),
                    "key_id": "generated_random"
                }
                st.session_state.view_mode = "show_article"
                st.rerun()
            except Exception as e:
                status.update(label="Temporal coverage failure!", state="error")
                st.error(f"Error running pipeline: {e}")

elif st.session_state.view_mode == "select_event" and st.session_state.custom_events:
    st.subheader(f"📅 Historical Events for {input_date}")
    st.write("Select an event to generate a dedicated Gonzo dispatch:")
    for event in st.session_state.custom_events:
        st.write(f"- **{event.year}**: {event.title}")
        safe_key = f"btn_event_{event.year}_{re.sub(r'[^a-zA-Z0-9]', '_', event.title)}"
        if st.button(
            f"🚀 Generate dispatch for {event.title}",
            key=safe_key
        ):
            with st.status(f"Connecting to temporal vortex for {event.title}...", expanded=True) as status:
                st.write("🛰️ Querying historical events via MCP Server...")
                st.write("🧠 Curating story with maximum dramatic tension...")
                st.write("📰 Drafting dispatch in Gonzo style...")
                try:
                    result = asyncio.run(run_pipeline_with_custom_event(event, input_date))
                    status.update(label="Dispatch complete!", state="complete", expanded=False)
                    st.session_state.active_article = {
                        "content": result.get("final_article", ""),
                        "published_path": result.get("published_path", ""),
                        "key_id": f"generated_custom_{event.year}"
                    }
                    st.session_state.custom_events = None
                    st.session_state.view_mode = "show_article"
                    st.rerun()
                except Exception as err:
                    status.update(label="Temporal coverage failure!", state="error")
                    st.error(f"Error running pipeline: {err}")

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

