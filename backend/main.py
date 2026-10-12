from dotenv import load_dotenv

load_dotenv()

import base64
import hashlib
import hmac
import logging
import math
import os
import random
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from embeddings import engine
from hints import get_category_hint
from morph import find_known_root
from words import DAILY_WORDS, EPOCH

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Settings ───────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]
# The daily word changes at local midnight. Kazakhstan is UTC+5.
DAY_TZ = timezone(timedelta(hours=float(os.getenv("DAY_UTC_OFFSET_HOURS", "5"))))
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = "dev-insecure-key"
    logger.warning("SECRET_KEY is not set; custom-game links use an insecure dev key.")

# Per-client request budget for /api/* (simple in-memory sliding window).
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))

# Secret words that actually exist in the loaded vocabulary (filled at startup).
playable_words: list[str] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading Kazakh word vectors…")
    await engine.load()
    playable_words[:] = [w for w in DAILY_WORDS if engine.word_exists(w)]
    missing = [w for w in DAILY_WORDS if not engine.word_exists(w)]
    if missing:
        logger.warning("%d daily words are not in the vocabulary and are skipped: %s",
                       len(missing), ", ".join(missing[:50]))
    if not playable_words:
        raise RuntimeError("No daily word exists in the loaded vocabulary.")
    logger.info("Engine ready. Vocab: %d, playable daily words: %d",
                len(engine.words), len(playable_words))
    yield


app = FastAPI(title="Жасырын Сөз API", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class RateLimiter:
    def __init__(self, limit: int, window: float = 60.0):
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        if len(self._hits) > 10_000:  # drop idle clients so memory stays bounded
            for k in [k for k, v in self._hits.items() if not v or now - v[-1] > self.window]:
                del self._hits[k]
        return True


rate_limiter = RateLimiter(RATE_LIMIT_PER_MIN)


def client_ip(request: Request) -> str:
    # Hugging Face / nginx put the real client first in X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/") and not rate_limiter.allow(client_ip(request)):
        return JSONResponse(status_code=429, content={"detail": {
            "code": "RATE_LIMITED", "message": "Тым көп сұраныс. Біраз күтіңіз."}})
    return await call_next(request)


# ── Game helpers ───────────────────────────────────────────────
def today_local():
    return datetime.now(DAY_TZ).date()


def get_game_id_for_today() -> int:
    return (today_local() - EPOCH).days


def game_id_to_word(game_id: int) -> str:
    return playable_words[game_id % len(playable_words)]


def rank_to_color(rank: int) -> str:
    if rank == 1:
        return "winner"
    if rank < 100:
        return "hot"
    if rank < 1000:
        return "warm"
    return "cold"


def rank_to_closeness_pct(rank: int, vocab_size: int) -> float:
    if rank == 1:
        return 100.0
    log_rank = math.log10(max(rank, 1))
    log_max = math.log10(max(vocab_size, 2))
    return round(max(0.0, (1 - log_rank / log_max) * 100), 1)


# Custom games are stateless: the token carries the word's vocab index plus an
# HMAC signature, so links survive restarts and work across several workers.
def _sign(idx: int, word: str) -> str:
    mac = hmac.new(SECRET_KEY.encode(), f"{idx}:{word}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac[:9]).decode().rstrip("=")


def make_custom_token(word: str) -> str:
    idx = engine.word_to_idx[word]
    return f"{idx:x}.{_sign(idx, word)}"


def resolve_custom_token(token: str) -> str:
    try:
        idx_hex, sig = token.split(".", 1)
        idx = int(idx_hex, 16)
        word = engine.words[idx]
    except (ValueError, IndexError):
        raise HTTPException(404, detail="Custom game not found.")
    if not hmac.compare_digest(sig, _sign(idx, word)):
        raise HTTPException(404, detail="Custom game not found.")
    return word


def resolve_secret(game_id: Optional[int], custom_token: Optional[str]) -> str:
    if custom_token:
        return resolve_custom_token(custom_token)
    if game_id is not None:
        if game_id < 0:
            raise HTTPException(422, detail="Invalid game_id.")
        return game_id_to_word(game_id)
    raise HTTPException(422, detail="Provide game_id or custom_token.")


def require_engine():
    if not engine.is_loaded() or not playable_words:
        raise HTTPException(503, detail="Engine not ready.")


def normalize_word(v: str) -> str:
    return " ".join(v.strip().lower().split())


def to_vocab_word(word: str) -> Optional[str]:
    """The word itself if known, else its root («жылқыны» → «жылқы»), else None."""
    if engine.word_exists(word):
        return word
    return find_known_root(word, engine.word_exists)


# ── Schemas ────────────────────────────────────────────────────
class GuessRequest(BaseModel):
    game_id: Optional[int] = None
    custom_token: Optional[str] = None
    guess: str

    @field_validator("guess")
    @classmethod
    def clean_guess(cls, v: str) -> str:
        cleaned = normalize_word(v)
        if not cleaned:
            raise ValueError("Guess cannot be empty")
        if len(cleaned) > 60:
            raise ValueError("Guess too long")
        return cleaned


class GuessResponse(BaseModel):
    rank: int
    color: str
    closeness_pct: float
    found: bool
    guess: str


class DailyResponse(BaseModel):
    game_id: int
    total_words: int
    date: str


class HintResponse(BaseModel):
    game_id: Optional[int]
    hint_type: str
    hint: str


class CustomGameRequest(BaseModel):
    word: str

    @field_validator("word")
    @classmethod
    def clean(cls, v: str) -> str:
        w = normalize_word(v)
        if not w:
            raise ValueError("Empty word")
        if len(w) > 40:
            raise ValueError("Too long")
        return w


class CustomGameResponse(BaseModel):
    custom_token: str


HintType = Literal["category", "letter", "length", "far_word", "mid_word", "close_word"]


# ── Endpoints ──────────────────────────────────────────────────
@app.get("/")
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "vocab_loaded": engine.is_loaded(),
        "vocab_size": len(engine.words),
        "daily_words": len(playable_words),
        "dummy_vectors": engine.is_dummy,
    }


@app.get("/api/daily", response_model=DailyResponse)
async def get_daily():
    require_engine()
    return DailyResponse(
        game_id=get_game_id_for_today(),
        total_words=len(playable_words),
        date=today_local().isoformat(),
    )


@app.get("/api/random")
async def get_random_game():
    require_engine()
    return {"game_id": random.randrange(len(playable_words)), "total_words": len(playable_words)}


@app.post("/api/custom", response_model=CustomGameResponse)
async def create_custom_game(body: CustomGameRequest):
    require_engine()
    word = to_vocab_word(body.word)
    if word is None:
        raise HTTPException(422, detail={"code": "WORD_NOT_FOUND",
                                         "message": f"«{body.word}» сөздікте жоқ."})
    return CustomGameResponse(custom_token=make_custom_token(word))


@app.post("/api/guess", response_model=GuessResponse)
async def submit_guess(body: GuessRequest):
    require_engine()
    secret = resolve_secret(body.game_id, body.custom_token)
    # Inflected guesses count as their root, which is what the response shows.
    guess = body.guess if body.guess == secret else to_vocab_word(body.guess)
    if guess is None:
        raise HTTPException(422, detail={"code": "WORD_NOT_FOUND",
                                         "message": f"Сөз табылмады: «{body.guess}»."})

    if guess == secret:
        return GuessResponse(rank=1, color="winner", closeness_pct=100.0, found=True, guess=guess)

    rank = engine.get_rank(secret, guess)
    if rank is None:
        raise HTTPException(500, detail="Could not compute rank.")

    return GuessResponse(
        rank=rank,
        color=rank_to_color(rank),
        closeness_pct=rank_to_closeness_pct(rank, len(engine.words)),
        found=False,
        guess=guess,
    )


def _neighbor_word(neighbors, start, end):
    pool = [w for w, _ in neighbors[start:end]]
    return pool[0] if pool else "?"


def build_hint(secret: str, hint_type: str, offset: int = 0) -> str:
    if hint_type == "letter":
        return f"Сөздің бірінші әрпі: «{secret[0].upper()}»"
    if hint_type == "length":
        return f"Сөздің ұзындығы: {len(secret)} әріп"
    if hint_type == "category":
        return get_category_hint(secret)

    neighbors = engine.get_top_similar(secret, topn=300)
    if hint_type == "far_word":
        return f"Алыс маңайдағы сөз (~200–300 орын): «{_neighbor_word(neighbors, 199, 300)}»"
    if hint_type == "mid_word":
        return f"Жақынырақ сөз (~50–80 орын): «{_neighbor_word(neighbors, 49, 80)}»"
    # close_word: each call (offset 0..9) reveals a different word from the top ~120
    start = 19 + offset * 10
    end = start + 10
    return f"Жақын сөз (~{start}–{end} орын): «{_neighbor_word(neighbors, start, end)}»"


@app.get("/api/hint/{game_id}", response_model=HintResponse)
async def get_hint(game_id: int, hint_type: HintType = "category",
                   offset: int = Query(0, ge=0, le=9)):
    require_engine()
    secret = resolve_secret(game_id, None)
    return HintResponse(game_id=game_id, hint_type=hint_type, hint=build_hint(secret, hint_type, offset))


@app.get("/api/hint/custom/{custom_token}", response_model=HintResponse)
async def get_custom_hint(custom_token: str, hint_type: HintType = "category",
                          offset: int = Query(0, ge=0, le=9)):
    require_engine()
    secret = resolve_custom_token(custom_token)
    return HintResponse(game_id=None, hint_type=hint_type, hint=build_hint(secret, hint_type, offset))


def _similar_payload(secret: str, word: str):
    # The list reveals the answer, so it is only given to someone who found it.
    if normalize_word(word) != secret:
        raise HTTPException(403, detail="Solve the game first.")
    similar = engine.get_top_similar(secret, topn=200)
    return {
        "secret": secret,
        "similar": [{"word": w, "rank": i + 2, "score": round(s, 4)}
                    for i, (w, s) in enumerate(similar)],
    }


@app.get("/api/similar/{game_id}")
async def get_similar_words(game_id: int, word: str = ""):
    require_engine()
    return _similar_payload(resolve_secret(game_id, None), word)


@app.get("/api/similar/custom/{custom_token}")
async def get_custom_similar(custom_token: str, word: str = ""):
    require_engine()
    return _similar_payload(resolve_custom_token(custom_token), word)


# Giving up: the client only asks for this when the player presses «Берілу».
@app.get("/api/reveal/{game_id}")
async def reveal_word(game_id: int):
    require_engine()
    return {"secret": resolve_secret(game_id, None)}


@app.get("/api/reveal/custom/{custom_token}")
async def reveal_custom_word(custom_token: str):
    require_engine()
    return {"secret": resolve_custom_token(custom_token)}


@app.get("/api/stats")
async def get_stats():
    return {
        "vocab_size": len(engine.words),
        "total_daily_words": len(playable_words),
        "today_game_id": get_game_id_for_today(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
