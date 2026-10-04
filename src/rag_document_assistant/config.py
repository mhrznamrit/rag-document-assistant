import asyncio
import os
import sys

from dotenv import load_dotenv


if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY is not set. "
        "Please add it to the .env file."
    )


if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please add it to the .env file."
    )


if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Please add it to the .env file."
    )


if not HF_TOKEN:
    raise ValueError(
        "HF_TOKEN is not set. "
        "Please add it to the .env file."
    )