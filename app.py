import asyncio
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent
# Page configuration for Streamlit
st.set_page_config(
    page_title="Chrono S. Thompson — Temporal Correspondent",
    page_icon="./avatar.svg",
    layout="wide"
)

OUTPUT_DIR = Path("storage/output")

state: ChronoState = {
    "target_date": datetime.now().strftime("%m/%d"),
    "raw_events": [],
    "curated_story": None,
    "modern_context": None,
    "final_article": None,
    "published_path": None,
    "custom_event": None,
    "filename": None
}

def list_saved_dispatches():
    """Reads the output directory and returns a list of saved .md files sorted by modification time."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(list(OUTPUT_DIR.glob("*.md")), reverse=True)

def fetch_events_for_date(target_date: str):
    """Auxiliary function to fetch historical events for a specific date."""
    from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
    state["target_date"] = target_date
    return asyncio.run(fetch_events_node(state))

async def run_pipeline():
    """Executes the full LangGraph pipeline for a given target date and returns the final state."""
    # Import tardio para inicializar apenas ao disparar
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    app = build_chrono_graph()
    return await app.ainvoke(state)

async def run_pipeline_with_custom_event(custom_event: HistoricalEvent):
    """Executes the full LangGraph pipeline for a given target date and a custom historical event."""
    from src.chrono_s_thompson.graph.builder import build_chrono_graph
    state["custom_event"] = custom_event
    app = build_chrono_graph()
    return await app.ainvoke(state)

# --- Generates the sidebar ---
with st.sidebar:
    st.header("⚙️ Painel de Operações")

    input_date = st.text_input(
        "Data Alvo (MM/DD):",
        value=datetime.now().strftime("%m/%d"),
        help="Informe o mês e dia para a cobertura temporal."
    )

    generate_btn = st.button("🚀 Random Dispatch", use_container_width=True, help="Generate a random dispatch for the selected date.")
    custom_event_btn = st.button("📅 Select Event", use_container_width=True, help="Generate a dispatch based on a selected historical event for the selected date.")

    st.divider()
    st.subheader("📁 Arquivo da Redação")
    saved_files = list_saved_dispatches()

    selected_file = None
    if saved_files:
        options = {f.name: f for f in saved_files}
        choice = st.selectbox("Escolha uma edição passada:", list(options.keys()))
        selected_file = options[choice]
    else:
        st.caption("Nenhum despacho arquivado.")


# --- Área Principal ---
col1, col2 = st.columns([0.08, 0.92])
with col1:
    st.image("./avatar.svg", width=120)

with col2:
    st.title("Chrono S. Thompson: The Gonzo Gazette")
    st.caption("Correspondente temporal autônomo através das eras.")

# Disparo de nova geração
if generate_btn:
    with st.status(f"Conectando ao vórtice temporal para {input_date}...", expanded=True) as status:
        st.write("🛰️ Consultando fatos históricos via MCP Server...")
        st.write("🧠 Curando a história com maior tensão dramática...")
        st.write("📰 Redigindo o despacho em estilo Gonzo...")

        try:
            result = asyncio.run(run_pipeline(input_date))
            status.update(label="Despacho concluído!", state="complete", expanded=False)
            st.success(f"Artigo publicado em: `{result.get('published_path')}`")
            
            # Exibe o conteúdo gerado
            st.markdown(result.get("final_article", "Erro: Artigo vazio."))
        except Exception as e:
            status.update(label="Falha na cobertura temporal!", state="error")
            st.error(f"Erro ao rodar pipeline: {e}")

elif custom_event_btn:
    if len(input_date.strip()) != 5 or input_date[2] != '/':
        st.error("Por favor, informe uma data alvo no formato MM/DD antes de selecionar um evento.")
    else:
        fetch_result = fetch_events_for_date(input_date)
        state["raw_events"] = fetch_result['raw_events']
        st.write("🛰️ Fatos históricos disponíveis:")
        for event in fetch_result['raw_events']:
            st.write(f"- {event['year']}: {event['title']}")
            st.button(f"Gerar despacho para {event['title']}", key=event['title'], on_click=lambda e=event: asyncio.run(run_pipeline_with_custom_event(e)))

# Leitura de arquivo selecionado na barra lateral
elif selected_file:
    st.subheader(f"Edição: {selected_file.stem}")
    content = selected_file.read_text(encoding="utf-8")
    st.markdown(content)

else:
    st.info("Selecione uma edição ao lado ou clique em **Gerar Despacho Temporal** para iniciar.")