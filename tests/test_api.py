from uuid import UUID

from fastapi.testclient import TestClient

from rag_document_assistant.auth import get_current_user_id
from rag_document_assistant.main import app


ALICE_ID = UUID("805a0620-5d66-4477-8501-d235745d806c")


class FakeRAGService:
    def answer_question(self, question: str, user_id: UUID) -> dict:
        return {
            "question": question,
            "answer": "Alice",
            "sources": [
                {
                    "source": "data\\documents\\alice_test.txt",
                    "file_type": "txt",
                    "content": "Alice owns this private document.",
                }
            ],
        }


def test_ask_requires_authentication():
    client = TestClient(app)

    response = client.post(
        "/ask",
        json={"question": "Who owns the private document?"},
    )

    assert response.status_code == 401


def test_ask_rejects_invalid_token():
    client = TestClient(app)

    response = client.post(
        "/ask",
        json={"question": "Who owns the private document?"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_authenticated_user_id_is_passed_to_rag_service():
    client = TestClient(app)

    app.state.rag_service = FakeRAGService()

    app.dependency_overrides[get_current_user_id] = lambda: ALICE_ID

    try:
        response = client.post(
            "/ask",
            json={"question": "Who owns the private document?"},
        )

        assert response.status_code == 200

        data = response.json()
        assert data["answer"] == "Alice"
        assert data["sources"][0]["source"].endswith("alice_test.txt")
    finally:
        app.dependency_overrides.clear()