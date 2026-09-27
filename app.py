import asyncio
from datetime import datetime
from pathlib import Path
import streamlit as st
from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent

# Page configuration for Streamlit
st.set_page_config(
    page_title="Chrono S. Thompson — Temporal Correspondent",
    page_icon="./avatar.svg",
    layout="wide"
)

OUTPUT_DIR = Path("storage/output")

state: ChronoState

def list_saved_dispatches():
    """Reads the output directory and returns a list of saved .md files sorted by modification time."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(list(OUTPUT_DIR.glob("*.md")), reverse=True)

def fetch_events_for_date(target_date: str):
    """Auxiliary function to fetch historical events for a specific date."""
    from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
    state.target_date = target_date
    return asyncio.run(fetch_events_node(state))

async def run_pipeline():
    """Executes the full LangGraph pipeline for a given target date and returns the final state."""
    # Late import to initialize only upon trigger
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    app = build_chrono_graph()
    return await app.ainvoke(state)

async def run_pipeline_with_custom_event(custom_event: HistoricalEvent):
    """Executes the full LangGraph pipeline for a given target date and a custom historical event."""
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    state.custom_event = custom_event
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
        choice = st.selectbox("Select a past edition:", list(options.keys()))
        selected_file = options[choice]
    else:
        st.caption("No archived dispatches.")


# --- Main Area ---
col1, col2 = st.columns([0.08, 0.92])
with col1:
    st.image("./avatar.svg", width=120)

with col2:
    st.title("Chrono S. Thompson: The Gonzo Gazette")
    st.caption("Autonomous temporal correspondent across eras.")

def render_article_with_translation(content: str, key_id: str = "article"):
    """Renders the article markdown with a button to translate it to Portuguese using Hugging Face transformers pipeline."""
    if not content:
        st.error("Empty article.")
        return

    col_space, col_btn = st.columns([0.7, 0.3])
    with col_btn:
        if st.button("🌐 Traduzir para PT (Transformers)", key=f"btn_translate_{key_id}"):
            with st.spinner("Traduzindo artigo via Hugging Face transformers pipeline (Helsinki-NLP/opus-mt-en-pt)..."):
                from src.chrono_s_thompson.core.translator import translate_markdown_text
                st.session_state[f"trans_cache_{key_id}"] = translate_markdown_text(content)

    translated_content = st.session_state.get(f"trans_cache_{key_id}")
    if translated_content:
        tab_pt, tab_en = st.tabs(["🇧🇷 Português", "🇺🇸 English (Original)"])
        with tab_pt:
            st.markdown(translated_content)
        with tab_en:
            st.markdown(content)
    else:
        st.markdown(content)

# Trigger new generation
if generate_btn:
    with st.status(f"Connecting to temporal vortex for {input_date}...", expanded=True) as status:
        st.write("🛰️ Querying historical events via MCP Server...")
        st.write("🧠 Curating story with maximum dramatic tension...")
        st.write("📰 Drafting dispatch in Gonzo style...")
        if input_date is None:
            status.update(label="Temporal coverage failure!", state="error")
            st.error(f"Input Date not Found")
        else:
            try:
                state.target_date = input_date
                result = asyncio.run(run_pipeline())
                status.update(label="Dispatch complete!", state="complete", expanded=False)
                st.success(f"Article published to: `{result.get('published_path')}`")

                final_article = result.get("final_article", "")
                render_article_with_translation(final_article, key_id="generated_random")
            except Exception as e:
                status.update(label="Temporal coverage failure!", state="error")
                st.error(f"Error running pipeline: {e}")

elif custom_event_btn:
    if type(input_date) != str or len(input_date.strip()) != 5 or input_date[2] != '/':
        st.error("Please provide a target date in MM/DD format before selecting an event.")
    else:
        fetch_result = fetch_events_for_date(input_date)
        state.raw_events = fetch_result['raw_events']
        st.write("🛰️ Available historical events:")
        for event in fetch_result['raw_events']:
            st.write(f"- {event['year']}: {event['title']}")
            st.button(f"Generate dispatch for {event['title']}", key=event['title'], on_click=lambda e=event: asyncio.run(run_pipeline_with_custom_event(e)))

# Reading selected file from sidebar
elif selected_file:
    st.subheader(f"Edition: {selected_file.stem}")
    content = selected_file.read_text(encoding="utf-8")
    render_article_with_translation(content, key_id=selected_file.stem)

else:
    st.info("Select a past edition from the sidebar or click **Random Dispatch** to start.")

