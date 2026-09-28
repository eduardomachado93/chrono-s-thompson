"""
This module provides helper functions for text cleaning and processing.
"""
import re
from bs4 import BeautifulSoup

def remove_html_tags(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def remove_references_section(text: str) -> str:
    """
    Removes the 'References', 'See also', and 'External links' sections from the given text.
    It looks for headings like '== References ==', '==See also==', etc., and removes everything that follows.
    """
    pattern = r"==\s*(references|see also|external links)\s*=="
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        return text[:match.start()].strip()
    return text

def remove_hyperlinks(text: str) -> str:
    """
    Remove HTML hyperlinks from the given text while preserving their labels.
    """
    soup = BeautifulSoup(text, "html.parser")
    for link in soup.find_all("a"):
        link.unwrap()
    return str(soup)

def remove_curly_brackets(text: str) -> str:
    """
    Remove text within curly brackets (e.g. Wiki templates {{...}}) from the given text.
    """
    return re.sub(r"\{\{.*?\}\}", "", text, flags=re.DOTALL)

def remove_image_and_file_captions(text: str) -> str:
    """
    Remove image/file thumbnail wikitext markup (e.g. thumb|250px|..., File:..., Image:...).
    """
    # Remove thumb/image parameter chains like thumb|250px|caption line
    text = re.sub(r"(?:thumb|upright|right|left|center|\d+px)\|[^\n]*", "", text, flags=re.IGNORECASE)
    # Remove file/image links like [[File:...]] or [[Image:...]]
    text = re.sub(r"\[\[(?:File|Image|Arquivo|Imagem):[^\]]+\]\]", "", text, flags=re.IGNORECASE)
    return text

def remove_section_headers(text: str) -> str:
    """
    Remove Wikipedia section header markup (e.g. === Dissolution === or == History ==).
    """
    return re.sub(r"={2,6}\s*[^=]+?\s*={2,6}", "", text)

def remove_wiki_links(text: str) -> str:
    """
    Remove wiki markup square brackets (e.g. [[Target|Label]] -> Label or [[Target]] -> Target).
    """
    return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)

def fix_spacing_and_artifacts(text: str) -> str:
    """
    Fix concatenated words/numbers (e.g. 13December -> 13 December) and normalize whitespace.
    """
    # Fix digit concatenated to capitalized month/word (e.g., 13December -> 13 December)
    text = re.sub(r"(\d{1,2})([A-Z][a-z]+)", r"\1 \2", text)
    # Normalize multiple blank lines to double newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # Normalize multiple horizontal spaces
    text = re.sub(r"[ \t]+", " ", text)
    return text

def clean_text(text: str) -> str:
    """
    Cleans the given text by removing HTML tags, wiki templates, reference sections, image captions, section headers, and wiki links.
    """
    text_without_hyperlink = remove_hyperlinks(text)
    text_without_html = remove_html_tags(text_without_hyperlink)
    text_without_curly_brackets = remove_curly_brackets(text_without_html)
    text_without_references = remove_references_section(text_without_curly_brackets)
    text_without_captions = remove_image_and_file_captions(text_without_references)
    text_without_headers = remove_section_headers(text_without_captions)
    text_without_wiki_links = remove_wiki_links(text_without_headers)
    cleaned_text = fix_spacing_and_artifacts(text_without_wiki_links)
    return cleaned_text.strip()
