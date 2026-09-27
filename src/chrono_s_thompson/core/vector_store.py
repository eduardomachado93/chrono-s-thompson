from functools import lru_cache

from src.config.settings import settings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

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