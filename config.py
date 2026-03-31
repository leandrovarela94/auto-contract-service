from decouple import config

APP_PORT = config("PORT", default=8080, cast=int)
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434", cast=str)
OLLAMA_MODEL = config("OLLAMA_MODEL", default="llama3.3", cast=str)
