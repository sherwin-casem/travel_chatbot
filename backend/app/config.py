from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> repo root is three levels up (app -> backend -> repo)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    booking_base_url: str = "https://www.example-travel.com/book"
    support_contact_url: str = "https://www.example-travel.com/support"
    support_contact_label: str = "Customer support"

    chroma_path: Path = _REPO_ROOT / "chroma_db"
    collection_name: str = "travel_knowledge"

    retrieval_top_k: int = 6
    similarity_threshold: float = 0.28

    data_dir: Path = _REPO_ROOT / "data"
    log_path: Path = _REPO_ROOT / "logs" / "conversations.jsonl"

    max_context_messages: int = 10

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    allow_local_onnx_embeddings: bool = False

    @field_validator("chroma_path", mode="before")
    @classmethod
    def parse_chroma_path(cls, v: str | Path | None) -> Path:
        if v is None or (isinstance(v, str) and not v.strip()):
            return _REPO_ROOT / "chroma_db"
        return Path(v) if not isinstance(v, Path) else v

    @field_validator("chroma_path", mode="after")
    @classmethod
    def resolve_chroma_path(cls, v: Path) -> Path:
        return v.resolve() if v.is_absolute() else (_REPO_ROOT / v).resolve()

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
