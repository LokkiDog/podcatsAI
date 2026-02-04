from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.podcast import PodcastResult, generate_podcast

app = FastAPI(title="Podcats AI")

INDEX_HTML = """
<!doctype html>
<html lang=\"ru\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Podcats AI</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 40px; max-width: 720px; }
      form { border: 1px solid #ddd; padding: 24px; border-radius: 12px; }
      input[type=file] { margin: 12px 0; }
      button { padding: 8px 16px; border-radius: 8px; border: none; background: #2f6fed; color: white; }
    </style>
  </head>
  <body>
    <h1>Podcats AI</h1>
    <p>Загрузите текстовый файл, чтобы получить аудио-подкаст по теме.</p>
    <form action=\"/generate\" method=\"post\" enctype=\"multipart/form-data\">
      <input type=\"file\" name=\"file\" accept=\".txt\" required />
      <button type=\"submit\">Сгенерировать</button>
    </form>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def build_metadata(result: PodcastResult) -> dict[str, object]:
    return {
        "outline": result.outline,
        "briefing": result.briefing,
        "script_preview": result.script.split("\n")[:12],
    }


@app.post("/generate")
async def generate(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse({"error": "Файл не найден"}, status_code=400)

    text = (await file.read()).decode("utf-8", errors="ignore").strip()
    if not text:
        return JSONResponse({"error": "Файл пустой"}, status_code=400)

    result = generate_podcast(text)
    response = FileResponse(
        path=result.audio_path,
        media_type="audio/mpeg",
        filename="podcast.mp3",
    )
    response.headers["X-Podcast-Metadata"] = str(build_metadata(result))
    return response


@app.get("/script")
def latest_script() -> dict[str, object]:
    audio_path = Path("output/podcast.mp3")
    if not audio_path.exists():
        return {"error": "Сначала сгенерируйте подкаст."}
    return {"message": "Аудио готово. Используйте /generate чтобы пересоздать."}
