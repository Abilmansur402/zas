"""
Kazakh word embeddings engine.

Loads pre-trained FastText Kazakh vectors (wiki.kk.vec, cleaned by
scripts/clean_vocab.py) and ranks the whole vocabulary by cosine similarity
to a secret word.

    engine = EmbeddingEngine()
    await engine.load()                        # once at startup
    engine.get_rank("үй", "есік")              # -> int, 1 = the secret itself
    engine.get_top_similar("үй", 10)           # -> [(word, score), ...]
"""

import asyncio
import logging
import os
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import numpy as np

from morph import same_family

logger = logging.getLogger(__name__)

VECTORS_PATH = Path(os.getenv("VECTORS_PATH", "./data/wiki.kk.clean.vec"))
CACHE_PATH = Path(os.getenv("CACHE_PATH", "./data/kk_vectors.npz"))
# Random vectors are only acceptable for local UI work and tests.
ALLOW_DUMMY_VECTORS = os.getenv("ALLOW_DUMMY_VECTORS", "0") == "1"
# How many secret words keep their full rank table in memory.
RANK_CACHE_SIZE = int(os.getenv("RANK_CACHE_SIZE", "64"))


class EmbeddingEngine:
    def __init__(self):
        self.words: list[str] = []
        self.vectors: Optional[np.ndarray] = None  # (N, dim), L2-normalised
        self.word_to_idx: dict[str, int] = {}
        self.is_dummy = False
        # secret word -> (rank table, order), see _ranking()
        self._rank_cache: "OrderedDict[str, tuple[np.ndarray, np.ndarray]]" = OrderedDict()
        self._loaded = False

    # ── Loading ────────────────────────────────────────────────
    async def load(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_sync)

    def _load_sync(self):
        if self._loaded:
            return

        if VECTORS_PATH.exists():
            if self._cache_is_fresh():
                logger.info("Loading cached vectors from %s", CACHE_PATH)
                self._load_from_cache()
                return
            logger.info("Loading FastText vectors from %s ...", VECTORS_PATH)
            self._load_from_vec_file()
            self._save_cache()
            return

        if CACHE_PATH.exists():
            logger.info("Vector file missing, using cache %s", CACHE_PATH)
            self._load_from_cache()
            return

        if not ALLOW_DUMMY_VECTORS:
            raise RuntimeError(
                f"Vector file not found at {VECTORS_PATH}. Download it with "
                "scripts/download_vectors.sh, or set ALLOW_DUMMY_VECTORS=1 "
                "for local UI development."
            )
        self._load_dummy_vectors()

    def _vec_signature(self) -> str:
        st = VECTORS_PATH.stat()
        return f"{VECTORS_PATH.name}:{st.st_size}:{int(st.st_mtime)}"

    def _cache_is_fresh(self) -> bool:
        if not CACHE_PATH.exists():
            return False
        try:
            with np.load(CACHE_PATH) as data:
                return str(data["source"]) == self._vec_signature()
        except Exception:  # old cache format, corrupted file, ...
            return False

    def _load_from_vec_file(self):
        words, vectors = [], []
        seen = set()
        with open(VECTORS_PATH, "r", encoding="utf-8") as f:
            header = f.readline().split()
            dim = int(header[1])
            for line in f:
                parts = line.rstrip().split(" ")
                if len(parts) != dim + 1:
                    continue
                word = parts[0].lower()
                if word in seen:
                    continue
                try:
                    vectors.append(np.asarray(parts[1:], dtype=np.float32))
                except ValueError:
                    continue
                words.append(word)
                seen.add(word)

        self.words = words
        self.vectors = np.vstack(vectors).astype(np.float32)
        self._normalize()
        self._build_index()
        self._loaded = True
        logger.info("Loaded %d word vectors (dim=%d).", len(words), dim)

    def _load_from_cache(self):
        with np.load(CACHE_PATH) as data:
            self.words = data["words"].tolist()
            self.vectors = data["vectors"]
        self._build_index()
        self._loaded = True
        logger.info("Loaded %d words from cache.", len(self.words))

    def _save_cache(self):
        try:
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            np.savez(
                CACHE_PATH,
                words=np.array(self.words),  # unicode array, no pickle needed
                vectors=self.vectors,
                source=np.array(self._vec_signature()),
            )
            logger.info("Saved vector cache to %s", CACHE_PATH)
        except OSError as e:
            logger.warning("Could not write vector cache: %s", e)

    def _load_dummy_vectors(self):
        from words import get_all_words

        rng = np.random.default_rng(42)
        self.words = list(dict.fromkeys(get_all_words()))
        self.vectors = rng.standard_normal((len(self.words), 50)).astype(np.float32)
        self._normalize()
        self._build_index()
        self.is_dummy = True
        self._loaded = True
        logger.warning("Loaded %d DUMMY vectors (dev mode, similarity is random).", len(self.words))

    def _normalize(self):
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        self.vectors = self.vectors / np.where(norms == 0, 1e-9, norms)

    def _build_index(self):
        self.word_to_idx = {w: i for i, w in enumerate(self.words)}

    # ── Queries ────────────────────────────────────────────────
    def is_loaded(self) -> bool:
        return self._loaded

    def word_exists(self, word: str) -> bool:
        return word in self.word_to_idx

    def get_vector(self, word: str) -> Optional[np.ndarray]:
        idx = self.word_to_idx.get(word)
        return None if idx is None else self.vectors[idx]

    def _similarities(self, word: str) -> np.ndarray:
        return self.vectors @ self.vectors[self.word_to_idx[word]]

    def _family_mask(self, secret: str) -> np.ndarray:
        """Other forms of the secret (жылқым, жылқышы) are kept out of the ranking."""
        mask = np.zeros(len(self.words), dtype=bool)
        prefix = secret[:2]
        for i, w in enumerate(self.words):
            if w.startswith(prefix) and same_family(w, secret):
                mask[i] = True
        return mask

    def _ranking(self, secret: str) -> tuple[np.ndarray, np.ndarray]:
        """(table, order): table[idx] = rank of words[idx]; order = indices by rank."""
        cached = self._rank_cache.get(secret)
        if cached is not None:
            self._rank_cache.move_to_end(secret)
            return cached

        sims = self._similarities(secret)
        sims[self.word_to_idx[secret]] = np.inf  # the secret is always rank 1
        family = self._family_mask(secret)
        sims[family] = -np.inf                   # forms of the secret go last in `order` ...
        order = np.argsort(-sims, kind="stable").astype(np.int32)
        table = np.empty(len(order), dtype=np.int32)
        table[order] = np.arange(1, len(order) + 1, dtype=np.int32)
        table[family] = 2                        # ... but count as "almost" when guessed

        self._rank_cache[secret] = (table, order)
        while len(self._rank_cache) > RANK_CACHE_SIZE:
            self._rank_cache.popitem(last=False)
        return table, order

    def get_rank(self, secret: str, guess: str) -> Optional[int]:
        """Rank of `guess` relative to `secret` (1 = the secret itself)."""
        if secret not in self.word_to_idx or guess not in self.word_to_idx:
            return None
        if secret == guess:
            return 1
        return int(self._ranking(secret)[0][self.word_to_idx[guess]])

    def get_top_similar(self, word: str, topn: int = 10) -> list[tuple[str, float]]:
        """Top-N most similar words to `word`, without the word and its own forms.

        Consistent with get_rank: the i-th entry has rank i + 2.
        """
        if word not in self.word_to_idx:
            return []
        _, order = self._ranking(word)
        sims = self._similarities(word)
        return [(self.words[i], float(sims[i])) for i in order[1 : topn + 1]]

    def get_similarity_score(self, word1: str, word2: str) -> Optional[float]:
        v1, v2 = self.get_vector(word1), self.get_vector(word2)
        if v1 is None or v2 is None:
            return None
        return float(np.dot(v1, v2))


engine = EmbeddingEngine()
