"""
API tests. They run the real engine on deterministic dummy vectors, so no
600 MB vector file is needed.

    cd backend
    pip install -r requirements.txt pytest
    pytest -q
"""

import os

os.environ["VECTORS_PATH"] = "./__no_vectors__.vec"
os.environ["CACHE_PATH"] = "./__no_cache__.npz"
os.environ["ALLOW_DUMMY_VECTORS"] = "1"
os.environ["SECRET_KEY"] = "test-key"
os.environ["RATE_LIMIT_PER_MIN"] = "0"  # tests below switch it on explicitly

import pytest
from fastapi.testclient import TestClient

import main
from main import app, game_id_to_word, rank_to_closeness_pct, rank_to_color


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs the lifespan, i.e. loads the engine
        yield c


def secret_for(client, game_id=0):
    return game_id_to_word(game_id)


def other_word(secret):
    return next(w for w in main.playable_words if w != secret)


# ── Health / daily ────────────────────────────────────────────
def test_health(client):
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["vocab_loaded"] is True
    assert data["daily_words"] > 0


def test_daily(client):
    data = client.get("/api/daily").json()
    assert isinstance(data["game_id"], int)
    assert data["total_words"] == len(main.playable_words)
    assert len(data["date"]) == 10


def test_random_in_range(client):
    for _ in range(20):
        gid = client.get("/api/random").json()["game_id"]
        assert 0 <= gid < len(main.playable_words)


def test_daily_words_have_no_spaces_and_no_duplicates():
    from words import DAILY_WORDS
    assert all(" " not in w for w in DAILY_WORDS)
    assert len(DAILY_WORDS) == len(set(DAILY_WORDS))


# ── Guess ─────────────────────────────────────────────────────
def test_correct_guess(client):
    secret = secret_for(client)
    data = client.post("/api/guess", json={"game_id": 0, "guess": secret.upper()}).json()
    assert data["found"] is True and data["rank"] == 1 and data["color"] == "winner"


def test_wrong_guess_rank(client):
    secret = secret_for(client)
    data = client.post("/api/guess", json={"game_id": 0, "guess": other_word(secret)}).json()
    assert data["found"] is False
    assert 2 <= data["rank"] <= len(main.engine.words)
    assert data["color"] in ("hot", "warm", "cold")


def test_rank_is_consistent_with_top_similar(client):
    secret = secret_for(client)
    top = main.engine.get_top_similar(secret, 5)
    for i, (w, _) in enumerate(top):
        assert main.engine.get_rank(secret, w) == i + 2


def test_guess_not_in_vocab(client):
    res = client.post("/api/guess", json={"game_id": 0, "guess": "жоқсөзжоқсөз"})
    assert res.status_code == 422
    assert res.json()["detail"]["code"] == "WORD_NOT_FOUND"


@pytest.mark.parametrize("guess", ["", "   ", "а" * 61])
def test_guess_validation(client, guess):
    assert client.post("/api/guess", json={"game_id": 0, "guess": guess}).status_code == 422


def test_guess_needs_a_game(client):
    assert client.post("/api/guess", json={"guess": "су"}).status_code == 422


def test_negative_game_id(client):
    assert client.post("/api/guess", json={"game_id": -1, "guess": "су"}).status_code == 422


# ── Custom games ──────────────────────────────────────────────
def test_custom_game_roundtrip(client):
    word = main.playable_words[3]
    token = client.post("/api/custom", json={"word": f"  {word.upper()} "}).json()["custom_token"]
    assert word not in token
    data = client.post("/api/guess", json={"custom_token": token, "guess": word}).json()
    assert data["found"] is True
    assert client.get(f"/api/hint/custom/{token}?hint_type=length").status_code == 200


def test_custom_token_tampering(client):
    token = client.post("/api/custom", json={"word": main.playable_words[3]}).json()["custom_token"]
    idx, sig = token.split(".")
    forged = f"{int(idx, 16) + 1:x}.{sig}"
    for bad in (forged, "zzz", "1.abc", ""):
        res = client.post("/api/guess", json={"custom_token": bad or "x", "guess": "су"})
        assert res.status_code == 404


def test_custom_unknown_word(client):
    res = client.post("/api/custom", json={"word": "жоқсөзжоқсөз"})
    assert res.status_code == 422


# ── Hints ─────────────────────────────────────────────────────
def test_hint_letter(client):
    secret = secret_for(client)
    data = client.get("/api/hint/0?hint_type=letter").json()
    assert secret[0].upper() in data["hint"]


@pytest.mark.parametrize("hint_type", ["category", "length", "far_word", "mid_word", "close_word"])
def test_hint_types(client, hint_type):
    assert client.get(f"/api/hint/0?hint_type={hint_type}").status_code == 200


def test_close_word_offsets_give_different_words(client):
    hints = {client.get(f"/api/hint/0?hint_type=close_word&offset={i}").json()["hint"] for i in range(10)}
    assert len(hints) == 10


def test_hint_validation(client):
    assert client.get("/api/hint/0?hint_type=nope").status_code == 422
    assert client.get("/api/hint/0?hint_type=close_word&offset=99").status_code == 422


# ── Similar (spoiler) ─────────────────────────────────────────
def test_similar_requires_solution(client):
    secret = secret_for(client)
    assert client.get("/api/similar/0").status_code == 403
    assert client.get(f"/api/similar/0?word={other_word(secret)}").status_code == 403
    data = client.get(f"/api/similar/0?word={secret}").json()
    assert data["secret"] == secret
    assert data["similar"][0]["rank"] == 2


# ── Inflected forms ───────────────────────────────────────────
def test_inflected_guess_counts_as_root(client):
    word = "жылқы"
    token = client.post("/api/custom", json={"word": word}).json()["custom_token"]
    for form in ["жылқыны", "жылқылардың", "жылқыға"]:
        r = client.post("/api/guess", json={"custom_token": token, "guess": form}).json()
        assert r["found"] is True and r["guess"] == word


def test_inflected_custom_word_uses_root(client):
    token = client.post("/api/custom", json={"word": "жылқыны"}).json()["custom_token"]
    assert client.get(f"/api/reveal/custom/{token}").json()["secret"] == "жылқы"


def test_same_family():
    from morph import same_family
    for form, root in [("жылқым", "жылқы"), ("жылқышы", "жылқы"), ("мектебі", "мектеп"), ("білегі", "білек"), ("кітабы", "кітап"),
                       ("судың", "су"), ("атты", "ат")]:
        assert same_family(form, root), form
    for other, root in [("ата", "ат"), ("сурет", "су"), ("балық", "бала"), ("жылқы", "жылқы")]:
        assert not same_family(other, root), other


# ── Give up / rate limit ──────────────────────────────────────
def test_reveal_daily(client):
    assert client.get("/api/reveal/3").json()["secret"] == game_id_to_word(3)


def test_reveal_custom(client):
    word = main.playable_words[0]
    token = client.post("/api/custom", json={"word": word}).json()["custom_token"]
    assert client.get(f"/api/reveal/custom/{token}").json()["secret"] == word
    assert client.get("/api/reveal/custom/0.bad").status_code == 404


def test_rate_limit(client):
    main.rate_limiter.limit = 3
    main.rate_limiter._hits.clear()
    try:
        codes = [client.get("/api/daily").status_code for _ in range(5)]
        assert codes == [200, 200, 200, 429, 429]
        assert client.get("/health").status_code == 200  # only /api/* is limited
    finally:
        main.rate_limiter.limit = 0
        main.rate_limiter._hits.clear()


# ── Stats & helpers ───────────────────────────────────────────
def test_stats(client):
    data = client.get("/api/stats").json()
    assert data["vocab_size"] > 0 and data["total_daily_words"] > 0


def test_rank_to_color():
    assert rank_to_color(1) == "winner"
    assert rank_to_color(50) == "hot"
    assert rank_to_color(500) == "warm"
    assert rank_to_color(5000) == "cold"


def test_rank_to_closeness_pct():
    assert rank_to_closeness_pct(1, 300000) == 100.0
    assert rank_to_closeness_pct(10, 300000) > rank_to_closeness_pct(100000, 300000)
    assert 0.0 <= rank_to_closeness_pct(10**7, 300000) <= 100.0


def test_rank_cache_is_bounded():
    from embeddings import RANK_CACHE_SIZE
    for w in main.playable_words[: RANK_CACHE_SIZE + 10]:
        main.engine.get_rank(w, main.playable_words[0])
    assert len(main.engine._rank_cache) <= RANK_CACHE_SIZE
