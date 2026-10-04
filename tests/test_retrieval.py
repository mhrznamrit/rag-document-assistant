from uuid import UUID

from rag_document_assistant.rag_service import RAGService


ALICE_ID = UUID("805a0620-5d66-4477-8501-d235745d806c")


class FakeVectorStore:
    def __init__(self):
        self.calls = []

    def similarity_search(self, question, k, filter):
        self.calls.append(
            {
                "question": question,
                "k": k,
                "filter": filter,
            }
        )
        return []


def test_retrieval_filters_by_user_id():
    service = object.__new__(RAGService)
    service.vectorstore = FakeVectorStore()

    documents = service.retrieve(
        question="Who owns the private document?",
        user_id=ALICE_ID,
    )

    assert documents == []
    assert service.vectorstore.calls == [
        {
            "question": "Who owns the private document?",
            "k": 3,
            "filter": {"user_id": str(ALICE_ID)},
        }
    ]