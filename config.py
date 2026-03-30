from decouple import config

APP_PORT= config("PORT", default=8080, cast=int)