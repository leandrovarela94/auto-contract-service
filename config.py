from decouple import config

APP_PORT = config("PORT", default=8080, cast=int)
GROQ_API_KEY = config("GROQ_API_KEY", default="", cast=str)
GEMINI_API_KEY = config("GEMINI_API_KEY", default="", cast=str)
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.3-70b-versatile", cast=str)
