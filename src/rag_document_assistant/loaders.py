from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader


def load_text_file(file_path: str | Path) -> list[Document]:
    """Load a plain text file into LangChain Document objects."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    text = path.read_text(encoding="utf-8")

    return [
        Document(
            page_content=text,
            metadata={
                "source": str(path),
                "file_type": "txt",
            },
        )
    ]


def load_pdf_file(file_path: str | Path) -> list[Document]:
    """Load a PDF file into LangChain Document objects."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    loader = PyPDFLoader(str(path))

    documents = loader.load()

    for document in documents:
        document.metadata["file_type"] = "pdf"

    return documents


def load_document(file_path: str | Path) -> list[Document]:
    """Load a supported document based on its file extension."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return load_text_file(path)

    if suffix == ".pdf":
        return load_pdf_file(path)

    raise ValueError(
        f"Unsupported file type: {suffix}. "
        "Supported types are: .txt, .pdf"
    )