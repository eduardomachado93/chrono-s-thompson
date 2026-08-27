from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import GONZO_WRITER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=settings.model_name,
    api_key=settings.openai_api_key.get_secret_value(),
    temperature=settings.temperature
)

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", GONZO_WRITER_SYSTEM_PROMPT),
    ("user", """LOCAL/DATA TEMPORAL: {target_date} de {year}
ACONTECIMENTO: {title}
DETALHES DO IMPACTO: {description}
ÂNGULO EDITORIAL GONZO: {hook}

PARALELO COM O PRESENTE:
{modern_context}

Escreva a reportagem completa com seu estilo visceral característico, tecendo o despacho histórico e a reflexão contemporânea final.""")
])


async def write_article_node(state: ChronoState) -> Dict[str, Any]:
    """Nó final de redação e persistência do artigo em formato Markdown.

    Args:
        state: Estado contendo 'curated_story', 'modern_context' e 'target_date'.

    Returns:
        Dicionário com as chaves 'final_article' e 'published_path'.
    """
    curated_story = state.get("curated_story")
    if not curated_story:
        logger.error("[Node: writer] Nenhuma história curada disponível para redação.")
        return {"final_article": None, "published_path": None}

    event = curated_story.selected_event
    hook = curated_story.gonzo_hook
    modern_context = state.get("modern_context", "Sem paralelo moderno registrado.")
    target_date = state.get("target_date", "Hoje")

    logger.info(
        f"[Node: writer] Redigindo despacho Gonzo para o evento de {event.year}: '{event.title}'..."
    )

    chain = writer_prompt | llm

    try:
        response = await chain.ainvoke({
            "target_date": target_date,
            "year": event.year,
            "title": event.title,
            "description": event.description,
            "hook": hook,
            "modern_context": modern_context
        })

        article_content = str(response.content)

        # Garante a existência do diretório de saída
        output_dir: Path = settings.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Gera o nome do arquivo padronizado: YYYY-MM-DD-YEAR.md
        now_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{now_str}_{event.year}_{safe_title}.md"
        file_path = output_dir / filename

        # Persiste o arquivo em disco
        file_path.write_text(article_content, encoding="utf-8")
        logger.info(f"[Node: writer] Artigo persistido com sucesso em: {file_path}")

        return {
            "final_article": article_content,
            "published_path": str(file_path)
        }

    except Exception as exc:
        logger.error(f"[Node: writer] Falha na geração do artigo: {exc}", exc_info=True)
        return {"final_article": None, "published_path": None}