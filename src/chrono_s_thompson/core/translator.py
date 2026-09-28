"""
Responsible for translating articles to Portuguese using transformers for the Streamlit App.
Reference: https://huggingface.co/docs/transformers/en/tasks/translation
"""
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict
from huggingface_hub import login
from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState

logger = logging.getLogger(__name__)

TRANSLATION_MODEL = settings.hf_translate_model
HF_TOKEN = settings.hf_token.get_secret_value()

@lru_cache(maxsize=1)
def get_translator_components(model_name: str = TRANSLATION_MODEL, hf_token: str = HF_TOKEN):
    """
    Lazy loads and caches the Hugging Face AutoTokenizer and AutoModelForSeq2SeqLM
    following the official Hugging Face Translation task documentation:
    https://huggingface.co/docs/transformers/en/tasks/translation
    """
    try:
        try:
            login(hf_token)
        except Exception:
            pass

        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

        logger.info(f"[Translator] Loading Hugging Face model and tokenizer for '{model_name}'...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        logger.info("[Translator] Model and tokenizer loaded successfully.")
        return tokenizer, model

    except Exception as exc:
        logger.error(f"[Translator] Failed to load transformers model/tokenizer: {exc}", exc_info=True)
        return None, None

def translate_markdown_text(text: str, model_name: str = TRANSLATION_MODEL) -> str:
    """
    Translates Markdown text paragraph by paragraph using Hugging Face AutoModelForSeq2SeqLM.
    Preserves images, headers, horizontal rules, code blocks, and metadata signatures.
    """
    if not text or not text.strip():
        return ""

    tokenizer, model = get_translator_components(model_name)
    if not tokenizer or not model:
        logger.warning("[Translator] Transformers model/tokenizer unavailable. Returning original text.")
        return text

    paragraphs = text.split("\n\n")
    translated_paragraphs = []

    for paragraph in paragraphs:
        stripped = paragraph.strip()
        # Preserve HTML images, markdown image lines, horizontal rules, metadata lines, code blocks
        if (
            not stripped
            or stripped.startswith("<img")
            or stripped.startswith("![")
            or stripped.startswith("---")
            or stripped.startswith("*— Chrono")
            or stripped.startswith("```")
        ):
            translated_paragraphs.append(paragraph)
            continue

        try:
            # Preserve headers (# Title -> # Tradução)
            header_prefix = ""
            text_to_translate = stripped
            if stripped.startswith("#"):
                parts = stripped.split(" ", 1)
                if len(parts) == 2 and all(c == "#" for c in parts[0]):
                    header_prefix = parts[0] + " "
                    text_to_translate = parts[1]

            inputs = tokenizer(text_to_translate, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = model.generate(inputs["input_ids"], attention_mask=inputs.get("attention_mask"), max_new_tokens=512)
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            translated_paragraphs.append(f"{header_prefix}{translated_text}")

        except Exception as err:
            logger.warning(f"[Translator] Error translating paragraph: {err}. Keeping original paragraph.")
            translated_paragraphs.append(paragraph)

    return "\n\n".join(translated_paragraphs)