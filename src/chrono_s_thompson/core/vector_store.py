"""
This module provides a function to create a vector store for semantic search and retrieval.
It uses OpenAIEmbeddings to convert the given texts into vectors and stores them in the vector store.
"""
from functools import lru_cache
from typing import Sequence, Union

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from config.settings import settings

def get_retriever(docs: Sequence[Union[Document, str]]) -> VectorStoreRetriever:
    if docs and isinstance(docs[0], Document):
        vectorstore = InMemoryVectorStore.from_documents(
            documents=list(docs),
            embedding=OpenAIEmbeddings(
                model=settings.embedding_model_name,
                api_key=settings.openai_api_key
            ),
        )
    else:
        vectorstore = InMemoryVectorStore.from_texts(
            texts=list(docs),
            embedding=OpenAIEmbeddings(
                model=settings.embedding_model_name,
                api_key=settings.openai_api_key
            ),
        )
    return vectorstore.as_retriever()