# Жасырын Сөз Paper Plan

## Thesis

Жасырын Сөз is not only a Kazakh semantic word-guessing game. It can be used as a reproducible testbed for evaluating Kazakh lexical semantic embeddings at the word level.

## Research Gap

Kazakh NLP has growing work on multilingual sentence encoders and downstream tasks, but there are still limited public resources for evaluating word-level lexical similarity. A game setting provides an interpretable way to compare model similarity with human intuition.

## Main Research Question

How well do available static and transformer-based embedding models capture Kazakh word-level semantic similarity, and where do they diverge from human judgments?

## Contributions

1. We introduce Жасырын Сөз, a Kazakh semantic guessing game inspired by Semantle and Contexto.
2. We release a curated Kazakh word list and document its categories and filtering decisions.
3. We create a native-speaker annotation set for Kazakh word-pair similarity.
4. We compare several embedding models using correlation with human scores and neighbor-quality analysis.
5. We analyze model errors related to morphology, loanwords, topical association, and polysemy.

## Minimum Study

The first paper should target a controlled evaluation rather than a large product launch.

- Vocabulary: curated core nouns from the game vocabulary.
- Human data: 150-300 annotated word pairs scored from 0 to 10.
- Models: FastText wiki.kk, FastText cc.kk, multilingual-e5, bge-m3, and kaz-embedder if feasible.
- Metrics: Spearman correlation, Pearson correlation, and qualitative top-neighbor evaluation.
- Secondary data: gameplay logs only if consent and deployment are ready in time.

## Method

1. Export the current vocabulary with categories.
2. Remove noisy items, inflected forms, Latin artifacts, and non-lemma entries.
3. Sample word pairs across high, medium, and low expected similarity bands.
4. Collect ratings from native Kazakh speakers.
5. Precompute embeddings for all vocabulary items.
6. Compute model similarity for the annotated pairs.
7. Compare model scores to human mean scores.
8. Inspect nearest neighbors for selected target words and categorize failure cases.

## Paper Structure

1. Introduction
2. Related Work
3. System Description
4. Vocabulary and Annotation Dataset
5. Embedding Models
6. Evaluation Method
7. Results
8. Error Analysis
9. Limitations and Ethics
10. Conclusion

## Immediate Work Items

1. Produce `vocabulary_export.csv`.
2. Produce `annotation_pairs_seed.csv`.
3. Manually review the seed pairs before sending them to annotators.
4. Prepare an annotation form with a 0-10 semantic similarity scale.
5. Implement evaluation scripts once the first human ratings are collected.

