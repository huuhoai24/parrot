from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from parrot.database import SubtitleStore
from parrot.sub_download import *

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(BASE_DIR / "templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="statics")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home(request: Request, q: str = ""):
    results = []
    transcripts = []
    if q.strip():
        with SubtitleStore() as store:
            match_video = store.get_videos(normalize(q))
            results = [dict(r) for r in match_video]

            transcripts = {}
            for vid in dict.fromkeys(r["video_id"] for r in match_video):
                transcripts[vid] = [dict(r) for r in store.get_text(vid)]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "parrot",
            "q": q,
            "results": results,
            "transcripts": transcripts,
            "total": len(results),
        },
    )
