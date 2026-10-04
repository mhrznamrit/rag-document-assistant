from uuid import UUID, uuid4

import psycopg

from rag_document_assistant.config import DATABASE_URL


def _connection_string() -> str:
    """Convert SQLAlchemy-style URL to a psycopg connection string."""
    return DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )


def create_user(
    email: str,
    password_hash: str,
) -> UUID:
    """Create a user and return the generated user ID."""
    user_id = uuid4()

    with psycopg.connect(_connection_string()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, email, password_hash),
            )

            created_user_id = cursor.fetchone()[0]

        connection.commit()

    return created_user_id


def get_user_by_email(email: str) -> tuple | None:
    """Return a user record by email."""
    with psycopg.connect(_connection_string()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            return cursor.fetchone()