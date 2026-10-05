"""Export paper-oriented vocabulary assets from backend/words.py.

The game vocabulary currently mixes curated category blocks with a noisy
fallback block named "Басқа". For the paper, these must be separated so the
dataset description can be honest and reproducible.
"""

from __future__ import annotations

import csv
import random
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORDS_FILE = ROOT / "backend" / "words.py"
OUT_DIR = ROOT / "paper" / "data"

CATEGORY_RE = re.compile(r"#\s*─+\s*(.*?)\s*─+")
WORD_RE = re.compile(r'"([^"]+)"')


def looks_clean_kazakh_word(word: str) -> bool:
    if not word:
        return False
    if any(ch.isascii() and ch.isalpha() for ch in word):
        return False
    if any(ch.isdigit() for ch in word):
        return False
    if any(ch in word for ch in ["/", "{", "}", "»", "—", "\u00a0"]):
        return False
    return True


def read_categorized_words() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    category = "Uncategorized"

    for line in WORDS_FILE.read_text(encoding="utf-8").splitlines():
        category_match = CATEGORY_RE.search(line)
        if category_match:
            category = category_match.group(1).strip()
            continue

        for word in WORD_RE.findall(line):
            rows.append(
                {
                    "word": word,
                    "category": category,
                    "source_split": "raw_other" if category == "Басқа" else "curated_core",
                    "is_clean_kazakh": "yes" if looks_clean_kazakh_word(word) else "no",
                }
            )

    return rows


def write_vocabulary(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "vocabulary_export.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["word", "category", "source_split", "is_clean_kazakh"],
        )
        writer.writeheader()
        writer.writerows(rows)


def generate_annotation_pairs(rows: list[dict[str, str]], n_per_band: int = 50) -> list[dict[str, str]]:
    rng = random.Random(20260929)
    curated = [
        row
        for row in rows
        if row["source_split"] == "curated_core" and row["is_clean_kazakh"] == "yes"
    ]

    by_category: dict[str, list[str]] = defaultdict(list)
    for row in curated:
        by_category[row["category"]].append(row["word"])

    categories = [cat for cat, words in by_category.items() if len(words) >= 4]

    pairs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add_pair(word_a: str, word_b: str, band: str, rationale: str) -> None:
        if word_a == word_b:
            return
        key = tuple(sorted((word_a, word_b)))
        if key in seen:
            return
        seen.add(key)
        pairs.append(
            {
                "word_a": word_a,
                "word_b": word_b,
                "sampling_band": band,
                "sampling_rationale": rationale,
                "human_score_0_10": "",
                "notes": "",
            }
        )

    # High-similarity candidates: same semantic category.
    while sum(1 for p in pairs if p["sampling_band"] == "high") < n_per_band:
        cat = rng.choice(categories)
        a, b = rng.sample(by_category[cat], 2)
        add_pair(a, b, "high", f"same category: {cat}")

    # Medium candidates: hand-picked broad relations likely to be associated but
    # not synonyms. These are intentionally mixed with random category sampling.
    related_category_pairs = [
        ("Табиғат", "Ауа райы"),
        ("Жануарлар", "Құстар"),
        ("Тамақ", "Жемістер"),
        ("Мектеп", "Ғылым"),
        ("Қала", "Көлік"),
        ("Үй", "Саймандар"),
        ("Медицина", "Дене"),
        ("Спорт", "Дене"),
        ("Сауда", "Мемлекет"),
        ("Дін", "Сезім"),
    ]
    while sum(1 for p in pairs if p["sampling_band"] == "medium") < n_per_band:
        cat_a, cat_b = rng.choice(related_category_pairs)
        if cat_a not in by_category or cat_b not in by_category:
            continue
        add_pair(
            rng.choice(by_category[cat_a]),
            rng.choice(by_category[cat_b]),
            "medium",
            f"related categories: {cat_a} / {cat_b}",
        )

    # Low-similarity candidates: distant random categories.
    while sum(1 for p in pairs if p["sampling_band"] == "low") < n_per_band:
        cat_a, cat_b = rng.sample(categories, 2)
        if {cat_a, cat_b} in [
            {"Табиғат", "Ауа райы"},
            {"Жануарлар", "Құстар"},
            {"Тамақ", "Жемістер"},
            {"Мектеп", "Ғылым"},
            {"Қала", "Көлік"},
        ]:
            continue
        add_pair(
            rng.choice(by_category[cat_a]),
            rng.choice(by_category[cat_b]),
            "low",
            f"different categories: {cat_a} / {cat_b}",
        )

    return pairs


def write_annotation_pairs(pairs: list[dict[str, str]]) -> None:
    path = OUT_DIR / "annotation_pairs_seed.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "word_a",
                "word_b",
                "sampling_band",
                "sampling_rationale",
                "human_score_0_10",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(pairs)

    annotator_path = OUT_DIR / "annotation_sheet.csv"
    with annotator_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["word_a", "word_b", "human_score_0_10", "notes"],
        )
        writer.writeheader()
        for pair in pairs:
            writer.writerow(
                {
                    "word_a": pair["word_a"],
                    "word_b": pair["word_b"],
                    "human_score_0_10": "",
                    "notes": "",
                }
            )

    pilot_pairs = []
    for band in ["high", "medium", "low"]:
        pilot_pairs.extend([p for p in pairs if p["sampling_band"] == band][:10])

    pilot_path = OUT_DIR / "pilot_annotation_sheet.csv"
    with pilot_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["word_a", "word_b", "human_score_0_10", "notes"],
        )
        writer.writeheader()
        for pair in pilot_pairs:
            writer.writerow(
                {
                    "word_a": pair["word_a"],
                    "word_b": pair["word_b"],
                    "human_score_0_10": "",
                    "notes": "",
                }
            )


def write_summary(rows: list[dict[str, str]], pairs: list[dict[str, str]]) -> None:
    curated = [r for r in rows if r["source_split"] == "curated_core"]
    raw_other = [r for r in rows if r["source_split"] == "raw_other"]
    clean_curated = [r for r in curated if r["is_clean_kazakh"] == "yes"]
    categories = sorted({r["category"] for r in curated})

    summary = [
        "# Paper Data Export",
        "",
        f"- Total words in backend/words.py: {len(rows)}",
        f"- Curated core words: {len(curated)}",
        f"- Clean Kazakh curated words: {len(clean_curated)}",
        f"- Raw other/noisy candidates: {len(raw_other)}",
        f"- Curated categories: {len(categories)}",
        f"- Seed annotation pairs: {len(pairs)}",
        "",
        "## Files",
        "",
        "- `vocabulary_export.csv`: word, category, source split, and a simple cleanliness flag.",
        "- `annotation_pairs_seed.csv`: initial 150 word pairs for native-speaker scoring. The sampling band is for dataset construction and should be hidden from annotators.",
        "- `annotation_sheet.csv`: annotator-facing version with only words, score, and notes.",
        "- `pilot_annotation_sheet.csv`: first 30 pairs for a 5-person pilot round.",
        "",
        "## Note",
        "",
        "The `Басқа` block contains noisy dictionary artifacts and should not be described as a clean paper vocabulary until it is filtered.",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_categorized_words()
    pairs = generate_annotation_pairs(rows)
    write_vocabulary(rows)
    write_annotation_pairs(pairs)
    write_summary(rows, pairs)
    print(f"Exported {len(rows)} words and {len(pairs)} annotation pairs to {OUT_DIR}")


if __name__ == "__main__":
    main()
