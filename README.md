# RAG Document Assistant

A production-oriented **Retrieval-Augmented Generation (RAG)** API for asking questions about uploaded documents.

The application allows authenticated users to upload TXT/PDF documents, converts document chunks into embeddings, stores them in PostgreSQL with pgvector, retrieves relevant chunks using semantic search, and uses a Groq-hosted LLM to generate grounded answers.

The project demonstrates practical AI engineering across **RAG, embeddings, vector databases, FastAPI, PostgreSQL, JWT authentication, authorization, Docker, and automated testing**.

---

## Features

- TXT and PDF document ingestion
- Document chunking for retrieval
- Hugging Face Sentence Transformer embeddings
- PostgreSQL + pgvector vector storage
- Semantic similarity search
- Groq LLM-based answer generation
- Source chunks returned with answers
- JWT authentication
- Argon2 password hashing
- Per-user document isolation
- Duplicate document detection
- 10 MB upload-size limit
- FastAPI REST API
- Docker Compose deployment
- Automated tests with pytest
- Automatic Swagger/OpenAPI documentation
- Environment-based secret configuration

---

## Architecture

```text
                         Client
                    Browser / Postman
                         / curl
                            |
                            v
                  +--------------------+
                  |      FastAPI       |
                  |      REST API      |
                  +---------+----------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
      +---------------+           +----------------+
      |     JWT       |           | Document Upload|
      | Authentication|           |    TXT / PDF   |
      +---------------+           +-------+--------+
                                          |
                                          v
                                  +---------------+
                                  | Document      |
                                  | Loader        |
                                  +-------+-------+
                                          |
                                          v
                                  +---------------+
                                  | Chunking      |
                                  +-------+-------+
                                          |
                                          v
                                  +---------------+
                                  | Hugging Face  |
                                  | Embeddings    |
                                  +-------+-------+
                                          |
                                          v
                            +---------------------------+
                            | PostgreSQL + pgvector     |
                            |                           |
                            | Document chunks           |
                            | Vector embeddings         |
                            | User ownership metadata   |
                            +-------------+-------------+
                                          |
                                          | Question
                                          v
                            +---------------------------+
                            | Semantic Similarity       |
                            | Retrieval                 |
                            +-------------+-------------+
                                          |
                                          v
                            +---------------------------+
                            | Retrieved Context         |
                            +-------------+-------------+
                                          |
                                          v
                            +---------------------------+
                            | Groq LLM                  |
                            | Grounded Generation       |
                            +-------------+-------------+
                                          |
                                          v
                            +---------------------------+
                            | Answer + Source Chunks    |
                            +---------------------------+
````

---

## RAG Pipeline

The application follows a standard retrieval-augmented generation pipeline:

```text
Upload Document
      |
      v
Load Document
      |
      v
Split into Chunks
      |
      v
Generate Embeddings
      |
      v
Store in PostgreSQL + pgvector
      |
      |
      | User asks a question
      v
Semantic Similarity Search
      |
      v
Retrieve Top 3 Chunks
      |
      v
Build Context
      |
      v
Groq LLM
      |
      v
Answer + Sources
```

### Document ingestion

TXT files are loaded directly and PDF files are processed using `PyPDFLoader`.

Documents are split into smaller chunks before embedding so that retrieval can target relevant sections rather than entire documents.

### Embeddings

The application uses a Hugging Face Sentence Transformer embedding model.

The current embedding dimension is:

```text
384
```

### Vector storage

Embeddings and document metadata are stored in PostgreSQL using the `pgvector` extension.

The main vector table is:

```text
document_embeddings
```

Relevant data includes:

```text
langchain_id
content
embedding
langchain_metadata
user_id
```

### Retrieval

Questions are matched against stored document embeddings using cosine similarity.

The application retrieves the top 3 relevant chunks:

```python
similarity_search(
    question,
    k=3,
    filter={"user_id": current_user_id}
)
```

The `user_id` filter is important because it prevents users from retrieving document chunks belonging to other users.

### Generation

Retrieved chunks are combined into a context and passed to the Groq-hosted LLM.

The prompt instructs the model to answer using only the retrieved context.

If the information cannot be found in the retrieved documents, the application instructs the model to respond:

```text
I don't have enough information in the provided documents.
```

---

## Authentication & Authorization

The API uses JWT bearer authentication.

### Registration

```http
POST /auth/register
```

Example:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Passwords are hashed using Argon2 through `pwdlib`.

---

### Login

```http
POST /auth/login
```

Example:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Response:

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

Protected endpoints use:

```http
Authorization: Bearer <JWT>
```

---

## User Data Isolation

Each user's uploaded documents are stored under their user ID:

```text
data/
└── documents/
    ├── <user-id-1>/
    │   └── document.txt
    └── <user-id-2>/
        └── document.txt
```

Vector records also contain the corresponding `user_id`.

Retrieval is always filtered using the authenticated user's ID.

Therefore:

```text
User A
  |
  +--> Can retrieve User A's documents
  |
  +--> Cannot retrieve User B's documents

User B
  |
  +--> Can retrieve User B's documents
  |
  +--> Cannot retrieve User A's documents
```

This provides application-level document ownership and retrieval isolation.

The application also prevents the same user from indexing the same document source multiple times.

---

## Tech Stack

| Category              | Technology                         |
| --------------------- | ---------------------------------- |
| Language              | Python 3.12                        |
| API                   | FastAPI                            |
| Server                | Uvicorn                            |
| RAG                   | LangChain                          |
| Embeddings            | Hugging Face Sentence Transformers |
| LLM                   | Groq                               |
| Vector Database       | PostgreSQL + pgvector              |
| Database Driver       | psycopg                            |
| Authentication        | JWT / PyJWT                        |
| Password Hashing      | Argon2 / pwdlib                    |
| Validation            | Pydantic                           |
| Testing               | pytest / httpx                     |
| Dependency Management | uv                                 |
| Containers            | Docker / Docker Compose            |

---

## Project Structure

```text
rag-document-assistant/
│
├── data/
│   └── documents/
│       └── <user-id>/
│           └── uploaded files
│
├── src/
│   └── rag_document_assistant/
│       ├── __init__.py
│       ├── auth.py
│       ├── chunking.py
│       ├── config.py
│       ├── embeddings.py
│       ├── loaders.py
│       ├── main.py
│       ├── rag_service.py
│       ├── schemas.py
│       ├── users.py
│       └── vectorstore.py
│
├── tests/
│   ├── test_api.py
│   └── test_retrieval.py
│
├── .dockerignore
├── .gitignore
├── .python-version
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
└── uv.lock
```

### Module responsibilities

**`main.py`**

FastAPI application and API endpoints.

**`auth.py`**

JWT creation/validation and password hashing/verification.

**`users.py`**

User persistence and database lookups.

**`loaders.py`**

TXT and PDF document loading.

**`chunking.py`**

Document splitting.

**`embeddings.py`**

Hugging Face embedding model configuration.

**`vectorstore.py`**

PostgreSQL/pgvector initialization, storage, retrieval configuration, and duplicate detection.

**`rag_service.py`**

Main RAG workflow:

```text
Load → Chunk → Embed → Store
                    ↓
Question → Retrieve → Context → LLM → Answer
```

**`schemas.py`**

Pydantic request and response models.

---

## API Endpoints

| Method | Endpoint            | Auth | Description                         |
| ------ | ------------------- | ---- | ----------------------------------- |
| GET    | `/`                 | No   | API status                          |
| GET    | `/health`           | No   | Health check                        |
| POST   | `/auth/register`    | No   | Register user                       |
| POST   | `/auth/login`       | No   | Login and receive JWT               |
| POST   | `/documents/upload` | Yes  | Upload and index document           |
| POST   | `/ask`              | Yes  | Ask question about user's documents |

---

## API Usage

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "healthy"
}
```

---

### Upload a Document

```http
POST /documents/upload
Authorization: Bearer <JWT>
Content-Type: multipart/form-data
```

Example with PowerShell:

```powershell
curl.exe -X POST http://127.0.0.1:8000/documents/upload `
  -H "Authorization: Bearer $TOKEN" `
  -F "file=@data/documents/sample.txt"
```

Example response:

```json
{
  "filename": "sample.txt",
  "file_type": "txt",
  "message": "Document uploaded and indexed successfully. Created 5 chunks."
}
```

The number of chunks depends on the document.

---

### Ask a Question

```http
POST /ask
Authorization: Bearer <JWT>
Content-Type: application/json
```

Request:

```json
{
  "question": "What is this document about?"
}
```

Response:

```json
{
  "question": "What is this document about?",
  "answer": "The document describes...",
  "sources": [
    {
      "source": "data/documents/<user-id>/sample.txt",
      "file_type": "txt",
      "content": "Relevant document content..."
    }
  ]
}
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://raguser:ragpassword@localhost:5433/ragdb

GROQ_API_KEY=your_groq_api_key

HF_TOKEN=your_huggingface_token

JWT_SECRET_KEY=your_long_random_secret
```

Never commit `.env` or API credentials to Git.

The `.gitignore` file already excludes `.env`.

### Docker database configuration

When running with Docker Compose, the application connects to PostgreSQL using the Docker service name:

```text
postgres:5432
```

The host machine exposes PostgreSQL on:

```text
localhost:5433
```

The API is exposed on:

```text
localhost:8000
```

---

## Local Development

### Requirements

* Python 3.12+
* uv
* PostgreSQL with pgvector
* Groq API key
* Hugging Face token

### Install dependencies

```powershell
uv sync
```

### Activate environment

```powershell
.venv\Scripts\Activate.ps1
```

### Start the API

```powershell
uv run uvicorn rag_document_assistant.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

---

## Docker Compose

The recommended way to run the complete application is Docker Compose.

Build and start:

```powershell
docker compose up -d --build
```

Check services:

```powershell
docker compose ps
```

The deployment contains:

```text
rag-api
rag-postgres
```

### API health

```powershell
curl.exe -i http://127.0.0.1:8000/health
```

Expected:

```text
HTTP/1.1 200 OK
```

### Stop services

```powershell
docker compose down
```

To remove the PostgreSQL volume as well:

```powershell
docker compose down -v
```

> `docker compose down -v` deletes the persistent PostgreSQL data.

---

## API Documentation

FastAPI automatically generates interactive API documentation.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

### OpenAPI Schema

```text
http://127.0.0.1:8000/openapi.json
```

Swagger UI can be used to manually test the API.

---

## Testing

Run the test suite:

```powershell
uv run pytest -v
```

Current tests cover:

* unauthenticated access rejection
* invalid JWT rejection
* authenticated user identity propagation
* retrieval filtering by `user_id`

Example result:

```text
4 passed
```

The retrieval isolation test verifies that vector search receives the authenticated user's ID:

```python
filter={"user_id": str(user_id)}
```

---

## Security

The application includes several security measures:

### Password security

Passwords are hashed using Argon2.

### JWT authentication

Protected endpoints require a valid bearer token.

### Authorization

Vector retrieval is restricted to the authenticated user's documents.

### File validation

Only `.txt` and `.pdf` uploads are accepted.

### Upload size limit

Uploads are limited to:

```text
10 MB
```

Larger files return:

```text
413 Request Entity Too Large
```

### Filename handling

Uploaded filenames are sanitized before being used to construct storage paths.

### Secret management

API keys, tokens, and JWT secrets are loaded from environment variables rather than being hardcoded.

---

## Configuration

Current RAG configuration includes:

```text
Embedding dimensions: 384
Retrieval top-k: 3
Distance strategy: Cosine similarity
Upload limit: 10 MB
LLM temperature: 0
```

The configured LLM is:

```text
openai/gpt-oss-20b
```

---

## Current Limitations

The project intentionally focuses on the core RAG backend.

Current limitations include:

* No frontend interface
* No conversation history
* No document deletion endpoint
* No document listing endpoint
* No streaming responses
* No background ingestion queue
* No OCR for scanned PDFs
* Fixed retrieval top-k
* No hybrid keyword + vector retrieval
* No reranking
* No automated CI/CD pipeline
* No Kubernetes deployment
* No production monitoring stack

---

## Future Improvements

Potential next steps include:

* Document management endpoints
* Document deletion and listing
* Streaming LLM responses
* Conversation history
* Hybrid search
* Reranking
* Configurable retrieval strategies
* OCR support
* RAG evaluation and benchmarking
* Structured logging
* Observability and monitoring
* GitHub Actions CI/CD
* Kubernetes deployment
* Cloud deployment
* Frontend application

---

## What This Project Demonstrates

This project provides hands-on implementation experience with:

### AI Engineering

* Retrieval-Augmented Generation
* LLM integration
* Text embeddings
* Semantic search
* Vector databases
* Grounded generation

### Backend Engineering

* FastAPI
* REST APIs
* Pydantic validation
* File uploads
* Authentication
* Authorization
* Error handling

### Data & Infrastructure

* PostgreSQL
* pgvector
* Docker
* Docker Compose
* Environment configuration

### Software Engineering

* Modular Python architecture
* Dependency management with uv
* Automated testing
* Security-conscious design

---

## Author

**Amrit Maharjan**

BSc CSIT | Data Science / AI / ML / Backend Development

---