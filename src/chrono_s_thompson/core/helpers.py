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

def remove_wiki_links(text: str) -> str:
    """
    Remove wiki markup square brackets (e.g. [[Target|Label]] -> Label or [[Target]] -> Target).
    """
    return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)

def clean_text(text: str) -> str:
    """
    Cleans the given text by removing HTML tags, wiki templates, wiki links, and reference sections.
    """
    text_without_hyperlink = remove_hyperlinks(text)
    text_without_html = remove_html_tags(text_without_hyperlink)
    text_without_curly_brackets = remove_curly_brackets(text_without_html)
    text_without_wiki_links = remove_wiki_links(text_without_curly_brackets)
    cleaned_text = remove_references_section(text_without_wiki_links)
    return cleaned_text.strip()
