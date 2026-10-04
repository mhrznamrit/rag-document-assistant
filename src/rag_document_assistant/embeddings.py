from langchain_huggingface import HuggingFaceEmbeddings

from rag_document_assistant.config import HF_TOKEN


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def create_embeddings() -> HuggingFaceEmbeddings:
    """Create and return the embedding model."""

    return HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={
            "token": HF_TOKEN,
        },
    )