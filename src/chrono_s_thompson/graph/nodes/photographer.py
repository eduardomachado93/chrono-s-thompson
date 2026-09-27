import logging
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
from openai import OpenAI

from config import settings
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import PHOTOGRAPHER_PROMPT

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.openai_api_key.get_secret_value()
)

async def take_photograph_node(state: ChronoState) -> Dict[str, Any]: 
    curated_story = state.get("curated_story")
    if not curated_story:
        logger.error("[Node: writer] Nenhuma história curada disponível para a foto.")
        return {"final_article": None, "published_path": None}

    event = curated_story.selected_event
    logger.info(
        f"[Node: writer] Tirando a foto do evento {event.year}: '{event.title}'..."
    )
    try:
        result = client.images.generate(
            model=settings.image_model_name,
            prompt=PHOTOGRAPHER_PROMPT.format(event_title=event.title),
            size="1024x1536",
            quality="low"
        )
        image_base64 = result.data[0].b64_json

        import base64
        image_bytes = base64.b64decode(image_base64)

        # Garante a existência do diretório de saída
        output_dir: Path = settings.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

         # Gera o nome do arquivo padronizado: YYYY-MM-DD-YEAR.md
        now_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{now_str}_photo_{event.year}_{safe_title}.png"
        file_path = output_dir / filename
        
        # Save the image to a file
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        return {
            "filename": filename
        }    
    except Exception as exc:
        logger.error(f"[Node: writer] Falha na geração do artigo: {exc}", exc_info=True)
        return {"final_article": None, "published_path": None}