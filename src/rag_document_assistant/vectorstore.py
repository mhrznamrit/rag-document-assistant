from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGEngine, PGVectorStore
from langchain_postgres.v2.indexes import DistanceStrategy

from rag_document_assistant.config import DATABASE_URL

TABLE_NAME = "document_embeddings"
VECTOR_SIZE = 384


def create_engine() -> PGEngine:
    """Create a PostgreSQL engine for the vector store."""
    return PGEngine.from_connection_string(DATABASE_URL)


def initialize_vectorstore_table(
    engine: PGEngine,
) -> None:
    """Create the pgvector table if it does not already exist."""
    import psycopg

    conninfo = DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )

    with psycopg.connect(conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
                """,
                (TABLE_NAME,),
            )
            table_exists = cursor.fetchone()[0]

    if table_exists:
        return

    engine.init_vectorstore_table(
        table_name=TABLE_NAME,
        vector_size=VECTOR_SIZE,
        overwrite_existing=False,
    )


def load_vectorstore(
    embeddings: Embeddings,
) -> PGVectorStore:
    """Load the PostgreSQL-backed vector store."""
    engine = create_engine()

    initialize_vectorstore_table(engine)

    return PGVectorStore.create_sync(
        engine=engine,
        embedding_service=embeddings,
        table_name=TABLE_NAME,
        distance_strategy=DistanceStrategy.COSINE_DISTANCE,
        metadata_columns=["user_id"],
        k=3,
    )


def add_documents_to_vectorstore(
    documents: list[Document],
    embeddings: Embeddings,
) -> PGVectorStore:
    """Add document chunks to the PostgreSQL vector store."""
    vectorstore = load_vectorstore(embeddings)

    vectorstore.add_documents(documents)

    return vectorstore


def document_already_indexed(source: str, user_id: str) -> bool:
    import psycopg

    conninfo = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)

    with psycopg.connect(conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 1
                FROM {TABLE_NAME}
                WHERE langchain_metadata->>'source' = %s
                  AND user_id = %s
                LIMIT 1
                """,
                (source, user_id),
            )
            return cursor.fetchone() is not None