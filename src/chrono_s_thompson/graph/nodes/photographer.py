import logging
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI

from config import settings
from src.chrono_s_thompson.core.state import ChronoState

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.openai_api_key.get_secret_value()
)

photograph_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    Award-winning candid documentary photograph by Magnum Photos, 35mm film grain, historical photojournalism. 

    In the scene, gonzo temporal correspondent Chrono S. Thompson (a sharp-featured man in his late 30s wearing a weathered white bucket hat, amber-tinted aviator sunglasses, a cigarette holder in his mouth, wearing a wrinkled khaki field shirt with a leather reporter shoulder strap and notepad in hand) is caught candidly amidst {HISTORICAL_EVENT_DESCRIPTION}.
    """)
])


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
            prompt=f"""
            First-person wide-angle selfie shot captured by an instant Polaroid camera, presented inside an authentic classic white Polaroid photo frame border. High-contrast pure black and white graphic novel art style in the aesthetic of Dark Horse Comics.

            Visual texture & medium: Printed on coarse aged newsprint paper with heavy mechanical halftone screen dot patterns, prominent vintage Ben-Day dots, rough black ink saturation, paper grain, and subtle printing press artifacts. Pure stark monochrome (pure black ink and paper white, zero gray wash).

            Foreground (The Selfie Perspective): Chrono S. Thompson is leaning in close to the wide-angle camera lens, his one arm extending off-frame toward the viewer as if pressing the shutter button. Chrono is smiling with a wild, grinning Gonzo expression: sharp facial features, wearing his signature weathered white bucket hat, dark aviator sunglasses reflecting the chaotic scene, a smoking cigarette holder clenched between his teeth, and an unbuttoned safari reporter shirt with a leather shoulder strap.

            Background (The Event): Directly behind and around Chrono, the full chaos of {event.title}.

            Gritty comic book inks, vintage Polaroid frame, authentic broadsheet newspaper print texture, vertical 4:5 or 1:1 format, 8k resolution.
            """,
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