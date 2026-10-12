"""
clean_vocab.py
==============
wiki.kk.vec ішінен жалғаулы формаларды (жылқыны, жылқының, жылқылары, ...) және
қазақша емес токендерді («жылқы»», abc, 123) алып тастайды.

Логика: сөздің соңынан жалғау кесіледі, егер
  1) қалған түбір сөздікте бар болса,
  2) түбір мен форма векторлары жеткілікті жақын болса (білім ≠ біл).
Слова дня (backend/words.py) әрқашан түбір деп саналады (жезде ≠ жез + -де).
Кесу қайталанады: жылқыларының → жылқылары → жылқы.
Тек түбір формалар қалады, 2 әріпті сөздер де (су, ат, үй).

Іске қосу (жоба түбірінен):
    python3 scripts/clean_vocab.py          # data/wiki.kk.vec → data/wiki.kk.clean.vec
    python3 scripts/clean_vocab.py check    # слова дня бар ма?
"""

import re
import sys
from pathlib import Path

import numpy as np

VECTORS_PATH = Path("data/wiki.kk.vec")
OUTPUT_VEC   = Path("data/wiki.kk.clean.vec")

# morph.py lives in backend/ locally and next to this script in the Docker build.
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent.parent / "backend")]
from morph import SHORT_SUFFIXES, stems  # noqa: E402

try:
    from words import DAILY_WORDS  # noqa: E402
except ImportError:
    DAILY_WORDS = []

# Curated daily words are known roots: never stripped (жезде ≠ жез + -де), and
# forms of them need less vector similarity to be folded in (атты → ат).
KNOWN_ROOTS = set(DAILY_WORDS)
MIN_COSINE = 0.4
MIN_COSINE_KNOWN_ROOT = 0.3
MIN_COSINE_SHORT = 0.5      # for one-letter endings: сиыры → сиыр, but жылы ≠ жыл
KAZAKH_WORD = re.compile(r"^[а-яәіңғүұқөһё]+(?:-[а-яәіңғүұқөһё]+)?$")


def is_kazakh(word: str) -> bool:
    return len(word) >= 2 and bool(KAZAKH_WORD.match(word))


def load_vectors(path: Path):
    print(f"Loading {path} ...")
    words, vecs, seen = [], [], set()
    with open(path, encoding="utf-8") as f:
        dim = int(f.readline().split()[1])
        for line in f:
            parts = line.rstrip().split(" ")
            if len(parts) != dim + 1:
                continue
            w = parts[0].lower()
            if w in seen or not is_kazakh(w):
                continue
            try:
                vecs.append(np.asarray(parts[1:], dtype=np.float32))
            except ValueError:
                continue
            words.append(w)
            seen.add(w)
    m = np.vstack(vecs)
    m /= np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)
    print(f"  {len(words):,} Kazakh tokens (dim={dim})")
    return words, m, dim


def find_root(word: str, idx: dict, m: np.ndarray, cache: dict) -> str:
    """Strips suffixes while the stem is a word with a similar vector."""
    if word in cache:
        return cache[word]
    root = word
    i = idx[word]
    candidates = [] if word in KNOWN_ROOTS else [
        *((s, False) for s in stems(word)),
        *((s, True) for s in stems(word, SHORT_SUFFIXES) if len(s) >= 3),
    ]
    for stem, short in candidates:
        j = idx.get(stem)
        if j is None:
            continue
        need = MIN_COSINE_SHORT if short else MIN_COSINE_KNOWN_ROOT if stem in KNOWN_ROOTS else MIN_COSINE
        if float(m[i] @ m[j]) < need:
            continue
        root = find_root(stem, idx, m, cache)
        break
    cache[word] = root
    return root


def clean_vectors():
    if not VECTORS_PATH.exists():
        sys.exit(f"{VECTORS_PATH} not found. Run scripts/download_vectors.sh first.")
    words, m, dim = load_vectors(VECTORS_PATH)
    idx = {w: i for i, w in enumerate(words)}
    cache: dict[str, str] = {}
    keep = [i for i, w in enumerate(words) if find_root(w, idx, m, cache) == w]
    print(f"  {len(keep):,} root forms kept, {len(words) - len(keep):,} inflected forms dropped")

    # Raw (un-normalised) values are not needed: the engine normalises anyway.
    with open(OUTPUT_VEC, "w", encoding="utf-8") as f:
        f.write(f"{len(keep)} {dim}\n")
        for i in keep:
            f.write(words[i] + " " + " ".join(f"{x:.5f}" for x in m[i]) + "\n")
    print(f"Wrote {OUTPUT_VEC}")


def check_words():
    if not DAILY_WORDS:
        print("words.py not found, skipping the daily word check.")
        return
    vocab = set()
    with open(OUTPUT_VEC, encoding="utf-8") as f:
        f.readline()
        for line in f:
            vocab.add(line.split(" ", 1)[0])
    missing = [w for w in DAILY_WORDS if w not in vocab]
    print(f"Daily words in vocabulary: {len(DAILY_WORDS) - len(missing)}/{len(DAILY_WORDS)}")
    if missing:
        print("Missing:", ", ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "check":
        clean_vectors()
    check_words()
