# Жасырын Сөз: paper-first roadmap

## Main Goal

Write a research paper using Жасырын Сөз as both:

1. A working Kazakh semantic word-guessing game.
2. A testbed for evaluating Kazakh lexical semantic embeddings.

The application is supporting infrastructure. The paper is the primary output.

## Core Paper Claim

Kazakh has limited public resources for evaluating word-level lexical semantic similarity. A semantic guessing game can provide:

- a reproducible interactive benchmark environment;
- a curated Kazakh noun vocabulary;
- human behavioral data about perceived semantic relatedness;
- an evaluation setup for comparing static and transformer-based embeddings.

## Tentative Title

Жасырын Сөз: A Semantic Word-Guessing Game as a Testbed for Kazakh Lexical Embeddings

## Paper Contributions

1. We present Жасырын Сөз, a Kazakh semantic word-guessing game inspired by Semantle and Contexto.
2. We describe a curated Kazakh word list for daily semantic guessing tasks.
3. We evaluate several embedding models for Kazakh word-level similarity.
4. We analyze where model similarity diverges from human intuition during gameplay.
5. We release code, vocabulary, and, if consent/logging is implemented, anonymized gameplay data.

## Minimum Publishable Study

The smallest credible paper should include:

- 300-1000 curated Kazakh nouns.
- 3-5 embedding models.
- 100-300 human-rated word pairs, or gameplay logs if enough users are available.
- Correlation between model similarity and human judgments.
- Qualitative error analysis for morphology, loanwords, polysemy, and topical association.

## Models To Compare

Baseline:

- FastText `wiki.kk.vec`
- FastText `cc.kk.300`

Stronger candidates:

- multilingual-e5-base or multilingual-e5-large
- BAAI/bge-m3
- kaz-embedder, if feasible to run offline

For transformer models, embeddings should be precomputed offline for the vocabulary. The game server should only load vectors and compute cosine similarity.

## Data Needed

### Vocabulary

Current repository has a curated `DAILY_WORDS` list. For the paper:

- document selection criteria;
- remove duplicates and inflected forms;
- split secret-word vocabulary from accepted-guess vocabulary;
- record categories for analysis.

### Human Judgments

Option A: annotation study.

- Create 100-300 Kazakh word pairs.
- Ask native speakers to rate semantic similarity from 0 to 10.
- Compute inter-annotator agreement.
- Compare model rankings using Spearman correlation.

Option B: gameplay logs.

- Add consent notice.
- Store anonymized guesses, ranks, timestamps, game id, and whether the user solved or surrendered.
- Analyze whether human guesses move closer to the target over time.

Best route: do both, but start with annotation because it is easier to control.

## Proposed Paper Structure

1. Abstract
2. Introduction
3. Related Work
4. Жасырын Сөз System
5. Vocabulary and Data Collection
6. Embedding Models
7. Evaluation Setup
8. Results
9. Error Analysis
10. Limitations and Ethics
11. Conclusion

## Key Experiments

### Experiment 1: Human Similarity Correlation

For each model:

- compute cosine similarity for annotated word pairs;
- compare against human average scores;
- report Spearman rho and Pearson r.

### Experiment 2: Neighbor Quality

For 50 secret words:

- collect top-20 nearest neighbors from each model;
- manually rate neighbor quality;
- categorize errors.

### Experiment 3: Gameplay Difficulty

For each daily word:

- number of guesses until solved;
- best rank reached;
- surrender rate;
- hint usage.

This requires logging and enough users, so it can be a secondary result or future work.

## Engineering Work Needed For The Paper

Priority 1:

- make model evaluation scripts;
- export current vocabulary to CSV;
- create word-pair annotation sheet;
- add reproducible vector precomputation.

Priority 2:

- add anonymous logging with consent;
- separate secret vocabulary from accepted guesses;
- close answer-leaking API endpoints.

Priority 3:

- polish UI and deploy public version;
- add archive, surrender, and share improvements.

## Recommended Next Step

Do not start by polishing the frontend. Start by building the research pipeline:

1. Export vocabulary.
2. Generate candidate word pairs.
3. Create annotation form or spreadsheet.
4. Precompute embeddings for at least FastText and one transformer model.
5. Produce the first results table.

Once the first results table exists, the paper becomes much easier to write.
