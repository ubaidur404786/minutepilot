import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "/data")))
    n8n_chat_url: str = os.getenv("N8N_CHAT_URL", "http://n8n:5678/webhook/minutepilot-chat")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    vision_model: str = os.getenv("VISION_MODEL", "qwen2.5vl:3b")
    whisper_model: str = os.getenv("WHISPER_MODEL", "small")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute: str = os.getenv("WHISPER_COMPUTE", "int8")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "200"))
    # n8n can wait a long time: a 20-minute recording takes minutes on CPU
    chat_timeout_s: int = int(os.getenv("CHAT_TIMEOUT_S", "1800"))


settings = Settings()
