from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from rag_document_assistant.auth import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from rag_document_assistant.users import create_user, get_user_by_email
from rag_document_assistant.rag_service import RAGService
from rag_document_assistant.schemas import (
    DocumentUploadResponse,
    QuestionRequest,
    QuestionResponse,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)


DOCUMENT_DIRECTORY = Path("data/documents")
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


app = FastAPI(
    title="RAG Document Assistant",
    description="A document question-answering API using Retrieval-Augmented Generation.",
    version="0.1.0",
)


rag_service = RAGService()


@app.get("/")
def root():
    return {
        "message": "RAG Document Assistant API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/auth/register")
def register(request: RegisterRequest):
    """Register a new user."""
    existing_user = get_user_by_email(request.email)

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists.",
        )

    password_hash = hash_password(request.password)

    user_id = create_user(
        email=request.email,
        password_hash=password_hash,
    )

    return {
        "message": "User registered successfully.",
        "user_id": str(user_id),
        "email": request.email,
    }


@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Authenticate a user and return a JWT access token."""
    user = get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    user_id, _, password_hash = user

    if not verify_password(
        request.password,
        password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
):
    """Upload and ingest a supported document."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in {".txt", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only .txt and .pdf files are supported."
            ),
        )

    user_document_directory = DOCUMENT_DIRECTORY / str(user_id)
    user_document_directory.mkdir(parents=True, exist_ok=True)

    destination = user_document_directory / filename

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file is too large. Maximum size is 10 MB.",
        )

    destination.write_bytes(content)

    # Use the test service when one is injected.
    # Otherwise, use the normal application service.
    service = getattr(app.state, "rag_service", rag_service)

    try:
        chunks_created = service.ingest_document(
            destination,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "filename": filename,
        "file_type": extension.lstrip("."),
        "message": (
            f"Document uploaded and indexed successfully. "
            f"Created {chunks_created} chunks."
        ),
    }


@app.post("/ask", response_model=QuestionResponse)
def ask_question(
    request: QuestionRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    service = getattr(app.state, "rag_service", rag_service)
    return service.answer_question(
        question=request.question,
        user_id=user_id,
    )