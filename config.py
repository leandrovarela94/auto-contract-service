from decouple import config

APP_PORT = config("PORT", default=8080, cast=int)
OLLAMA_API_KEY = config("OLLAMA_API_KEY", default="", cast=str)
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="https://ollama.com/v1", cast=str)
OLLAMA_MODEL = config("OLLAMA_MODEL", default="llama3.2", cast=str)
