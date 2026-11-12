from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from parrot.database import CardStore, SubtitleStore
from parrot.fetch_subtitles import normalize

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(BASE_DIR / "templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="statics")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/search")
def api_saerch(q: str = ""):
    results = []
    if q.strip():
        with SubtitleStore() as store:
            results = store.get_videos(normalize(q))
    return {
        "q": q,
        "results": results,
    }


@app.get("/api/transcript")
def get_transcript(video_id: str):
    transcript = []
    with SubtitleStore() as store:
        transcript = store.get_text(video_id)
    return {"video_id": video_id, "transcript": transcript}


class CardIn(BaseModel):
    front: str | None = None  # tình huống có thể để trống (bổ sung sau)
    back: str
    video_id: str
    start_time: int
    end_time: int


@app.get("/study")
def study_page(request: Request):
    return templates.TemplateResponse(request, "study.html")


@app.post("/api/cards")
def create_card(card: CardIn):
    with CardStore() as store:
        card_id = store.add_card(
            card.front, card.back, card.video_id, card.start_time, card.end_time
        )
    return {"id": card_id}


@app.get("/api/study/due")
def due_cards(limit: int = 20):
    with CardStore() as store:
        return {"cards": store.get_due(limit)}


@app.post("/api/cards/{card_id}/review")
def review_card(card_id: int, rating: Literal["again", "hard", "good", "easy"]):
    with CardStore() as store:
        state = store.apply_review(card_id, rating)
    return {"card_id": card_id, **state}


@app.post("/api/study/reset")
def reset_cards():
    with CardStore() as store:
        reset = store.reset_all()
    return {"reset": reset}
