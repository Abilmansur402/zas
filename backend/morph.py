"""
Minimal Kazakh suffix stripping, shared by scripts/clean_vocab.py (to drop
inflected forms from the vocabulary) and the API (to map a guess like
«жылқыны» to the root «жылқы» that is in the vocabulary).
"""

from typing import Callable, Iterator

# Longest first. Single-letter endings (-ы, -і, -а, -н, -м) are left out on
# purpose: they collide with the root's own last letter too often.
SUFFIXES = sorted({
    # Plural, plural + possessive
    "лар", "лер", "дар", "дер", "тар", "тер",
    "лары", "лері", "дары", "дері", "тары", "тері",
    # Genitive (+ the common Wikipedia misspelling with н instead of ң)
    "ның", "нің", "дың", "дің", "тың", "тің",
    "нын", "нін", "дын", "дін", "тын", "тін",
    # Accusative
    "ны", "ні", "ды", "ді", "ты", "ті",
    # Dative
    "ға", "ге", "қа", "ке", "на", "не",
    # Locative
    "да", "де", "та", "те", "нда", "нде",
    # Ablative
    "дан", "ден", "тан", "тен", "нан", "нен",
    # Instrumental
    "мен", "бен", "пен", "менен",
    # Possessive
    "сы", "сі", "ым", "ім", "ың", "ің", "ымыз", "іміз", "ыңыз", "іңіз",
    # -дағы, -дікі, -дай, -сыз, -лы
    "дағы", "дегі", "тағы", "тегі", "дікі", "тікі", "нікі",
    "дай", "дей", "тай", "тей", "сыз", "сіз", "лы", "лі",
}, key=len, reverse=True)

# Single letters: possessive -ы/-і (+ accusative -н), 1st person -м. Only used
# when the vectors confirm the stem (see scripts/clean_vocab.py).
SHORT_SUFFIXES = ("ы", "і", "н", "м")

MIN_STEM = 2


def stems(word: str, suffixes=SUFFIXES) -> Iterator[str]:
    """Candidate stems of `word`, one suffix removed, longest suffix first."""
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= MIN_STEM:
            yield word[: -len(suf)]


def find_known_root(word: str, is_known: Callable[[str], bool], depth: int = 3) -> str | None:
    """Strips suffixes (up to `depth` times) until a known word is reached."""
    if depth == 0:
        return None
    for stem in stems(word):
        if is_known(stem):
            return stem
        deeper = find_known_root(stem, is_known, depth - 1)
        if deeper:
            return deeper
    return None


def same_family(word: str, root: str) -> bool:
    """True for other forms and derivatives of `root` (жылқым, жылқышы, мектебі).

    Long roots compare by prefix, without the last letter when it can mutate
    (мектеп → мектебі, білек → білегі); short roots (су, ат) only by suffix
    stripping, so «ата» is not a form of «ат».
    """
    if word == root:
        return False
    if len(root) >= 6 or (len(root) >= 4 and root[-1] in "кқп"):
        return word.startswith(root[:-1])
    if len(root) >= 4:
        return word.startswith(root)
    return word.startswith(root) and find_known_root(word, lambda s: s == root) == root
