from pathlib import Path
from uuid import UUID

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

from rag_document_assistant.chunking import split_documents
from rag_document_assistant.loaders import load_document
from rag_document_assistant.config import GROQ_API_KEY
from rag_document_assistant.embeddings import create_embeddings
from rag_document_assistant.vectorstore import (
    add_documents_to_vectorstore,
    document_already_indexed,
    load_vectorstore,
)


MODEL_NAME = "openai/gpt-oss-20b"


class RAGService:
    """Application-level RAG service."""

    def __init__(self):
        print("Initializing RAG service...")

        print("Loading embedding model...")
        self.embeddings: HuggingFaceEmbeddings = create_embeddings()

        self._ensure_vectorstore()

        print("Loading PostgreSQL vector store...")
        self.vectorstore = load_vectorstore(
            embeddings=self.embeddings,
        )

        print("Loading Groq LLM...")
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=MODEL_NAME,
            temperature=0,
        )

        print("RAG service initialized.")

    def _ensure_vectorstore(self) -> None:
        """Ensure the PostgreSQL vector store table exists."""
        from rag_document_assistant.vectorstore import (
            create_engine,
            initialize_vectorstore_table,
        )

        print("Initializing PostgreSQL vector store...")
        engine = create_engine()
        initialize_vectorstore_table(engine)
        print("PostgreSQL vector store ready.")

    def retrieve(self, question: str, user_id: UUID) -> list[Document]:
        """Retrieve relevant documents."""

        return self.vectorstore.similarity_search(
            question,
            k=3,
            filter={"user_id": str(user_id)},
        )

    def build_context(self, documents: list[Document]) -> str:
        """Build the context passed to the language model."""

        return "\n\n".join(
            document.page_content
            for document in documents
        )

    def build_prompt(
        self,
        question: str,
        context: str,
    ) -> str:
        """Build the prompt used for answer generation."""

        return f"""
    You are a helpful document question-answering assistant.

    Answer the user's question using ONLY the information
    provided in the context below.

    If the answer cannot be found in the context, say:
    "I don't have enough information in the provided documents."

    Context:
    ----------------
    {context}
    ----------------

    Question:
    {question}

    Answer:
    """

    def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """Generate an answer using the LLM."""

        prompt = self.build_prompt(
            question=question,
            context=context,
        )

        response = self.llm.invoke(prompt)

        return response.content

    def ingest_document(
        self,
        file_path: str | Path,
        user_id: UUID,
    ) -> int:
        """Ingest a document and update the PostgreSQL vector store."""

        print(f"Ingesting document: {file_path}")

        source = str(file_path)

        if document_already_indexed(
            source=source,
            user_id=str(user_id),
        ):
            raise ValueError(
                f"Document is already indexed: {source}"
            )

        documents = load_document(file_path)

        print(f"Loaded {len(documents)} document page(s).")

        chunks = split_documents(documents)

        for chunk in chunks:
            chunk.metadata["user_id"] = str(user_id)

        if not chunks:
            raise ValueError(
                f"No chunks were created from document: {source}"
            )

        print(f"Created {len(chunks)} chunks.")

        add_documents_to_vectorstore(
            documents=chunks,
            embeddings=self.embeddings,
        )

        self.vectorstore = load_vectorstore(
            embeddings=self.embeddings,
        )

        print("Document added to vector store.")

        return len(chunks)

    def answer_question(self, question: str, user_id: UUID) -> dict:
        """Generate an answer using retrieved document context."""

        documents = self.retrieve(question=question, user_id=user_id)

        context = self.build_context(documents)

        answer = self.generate_answer(
            question=question,
            context=context,
        )

        sources = [
            {
                "source": document.metadata.get("source"),
                "file_type": document.metadata.get("file_type"),
                "content": document.page_content,
            }
            for document in documents
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }