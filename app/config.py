from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    booking_base_url: str = "https://www.example-travel.com/book"
    support_contact_url: str = "https://www.example-travel.com/support"
    support_contact_label: str = "Customer support"

    chroma_path: str = "./chroma_db"
    collection_name: str = "travel_knowledge"

    retrieval_top_k: int = 6
    similarity_threshold: float = 0.28

    data_dir: Path = Path("data")
    log_path: Path = Path("logs/conversations.jsonl")

    max_context_messages: int = 10


settings = Settings()
