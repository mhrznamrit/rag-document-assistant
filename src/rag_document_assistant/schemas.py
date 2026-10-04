from pydantic import BaseModel, EmailStr, Field, field_validator


 
class RegisterRequest(BaseModel):
    """Request body for user registration."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)



class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT authentication response."""

    access_token: str
    token_type: str = "bearer"


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask about the knowledge base.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


class Source(BaseModel):
    source: str | None = None
    file_type: str | None = None
    content: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]


class DocumentUploadResponse(BaseModel):
    filename: str
    file_type: str
    message: str