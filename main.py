"""
Auto Contract Service — FastAPI Backend
Gerador de propostas e contratos com IA usando Ollama Cloud.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import APP_PORT
from routes.analyze import router as analyze_router
from routes.templates import router as templates_router

app = FastAPI(
    title="Auto Contract Service",
    description="Gerador de propostas com IA",
    version="3.0.0",
    docs_url="/docs",
    redoc_url=None,
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(analyze_router)
app.include_router(templates_router)


@app.get("/")
async def root():
    from fastapi.responses import FileResponse

    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    print(f"\n{'=' * 50}")
    print("  Auto Contract Service")
    print(f"{'=' * 50}")
    print(f"  http://127.0.0.1:{APP_PORT}")
    print(f"  Docs: http://127.0.0.1:{APP_PORT}/docs")
    print(f"{'=' * 50}\n")
    uvicorn.run("main:app", host="0.0.0.0", port=APP_PORT, reload=False)
