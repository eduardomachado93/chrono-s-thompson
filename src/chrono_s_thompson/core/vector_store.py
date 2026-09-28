"""
This module provides a function to create a vector store for semantic search and retrieval.
It uses OpenAIEmbeddings to convert the given texts into vectors and stores them in the vector store.
"""
from functools import lru_cache

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from src.config.settings import settings

@lru_cache(maxsize=1)
def get_retriever(docs: list[str]) -> VectorStoreRetriever:
    vectorstore = InMemoryVectorStore.from_texts(
        texts=docs,
        embedding=OpenAIEmbeddings(
            model=settings.embedding_model_name,
            api_key=settings.openai_api_key
        ),
    )
    return vectorstore.as_retriever()