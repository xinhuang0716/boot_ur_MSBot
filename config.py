import os


class DefaultConfig:
    """Reads Bot Framework settings from environment variables."""

    # Bot Framework service port
    BOT_PORT: int = int(os.environ.get("BOT_PORT", 3978))

    # Azure Bot application credentials (can be left empty for local testing)
    APP_ID: str = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD: str = os.environ.get("MicrosoftAppPassword", "")

    # Ollama LLM settings
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

    # Conversation history
    HISTORY_LIMIT: int = int(os.environ.get("HISTORY_LIMIT", 20))
