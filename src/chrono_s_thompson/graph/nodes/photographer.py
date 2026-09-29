"""
Node responsible for generating visual illustrations for curated stories in the Chrono S. Thompson LangGraph workflow.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI
from pydantic import FilePath

from config import settings
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import PHOTOGRAPHER_PROMPT

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.openai_api_key.get_secret_value()
)

async def take_photograph_node(state: ChronoState) -> Dict[str, Any]: 
    """Node in the LangGraph responsible for synthesizing an image based on the curated story.

    Args:
        state: The current state of the pipeline containing `curated_story`.

    Returns:
        A dictionary with `photo_file_path` and `photo_filename` to partially mutate ChronoState, or an error payload.
    """
    curated_story = state.curated_story
    if not curated_story:
        return {"error": True, "error_msg": "[Node: photographer] No curated story available for the photo."}

    event = curated_story.selected_event
    logger.info(
        f"[Node: photographer] Taking photograph of event {event.year}: '{event.title}'..."
    )
    try:
        result = client.images.generate(
            model=settings.image_model_name,
            prompt=PHOTOGRAPHER_PROMPT.format(photo_description=curated_story.photo_description),
            size="1024x1536",
            quality="low"
        )
        image_base64 = result.data[0].b64_json

        import base64
        image_bytes = base64.b64decode(image_base64)

        # Ensure output directory exists
        images_dir: Path = settings.images_dir
        images_dir.mkdir(parents=True, exist_ok=True)

        # Generate standardized file name: YYYY-MM-DD_photo_YEAR_title.png
        now_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{now_str}_photo_{event.year}_{safe_title}.png"
        file_path = images_dir / filename
        
        # Save the image to a file
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        return {
            "photo_file_path": FilePath(file_path),
            "photo_filename": filename,
        }    
    except Exception as exc:
        return {"error": True, "error_msg": f"[Node: photographer] Failed to generate photo: {exc}"}