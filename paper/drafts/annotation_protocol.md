# Annotation Protocol

## Task

Annotators rate the semantic similarity of two Kazakh words.

The question shown to annotators should be:

How similar in meaning are these two Kazakh words?

## Scale

Use an integer score from 0 to 10.

- 0: completely unrelated
- 1-2: very weakly related
- 3-4: loosely associated but not similar
- 5-6: clearly related or same broad topic
- 7-8: strongly similar or same semantic class
- 9-10: nearly identical in meaning, synonym-like, or very close variants

Annotators should rate semantic similarity, not spelling similarity.

## Instructions For Annotators

1. Read both words carefully.
2. Rate meaning similarity from 0 to 10.
3. Use your first natural judgment.
4. Do not search online unless the word is completely unfamiliar.
5. If one or both words are unfamiliar, leave a note.
6. If the pair feels related only because both belong to a broad category, avoid giving the maximum score.

## Data Columns

The annotation sheet should contain only these visible columns:

- `word_a`
- `word_b`
- `human_score_0_10`
- `notes`

The `sampling_band` and `sampling_rationale` columns from `annotation_pairs_seed.csv` should be hidden from annotators. They are for dataset construction and later analysis only.

## Pilot Round

Start with 5 annotators and 30 pairs.

Check:

- whether the scale is understandable;
- whether many words are unfamiliar;
- whether pairs need clearer instructions;
- whether annotators use the full score range.

After the pilot, revise the pair list before collecting the full dataset.

## Full Round

Target:

- 150-300 word pairs;
- at least 3 independent ratings per pair;
- preferably 5 ratings per pair if time allows.

For each pair, report:

- mean human score;
- standard deviation;
- number of annotators;
- optional flag for high disagreement.

## Quality Control

Add 10-15 repeated or near-repeated pairs to estimate consistency. These should not be obvious to annotators.

Remove or flag:

- pairs where most annotators mark a word as unfamiliar;
- pairs with extremely high disagreement;
- entries with missing scores;
- annotators who give the same score to nearly every pair.

## Ethics

The annotation does not need personal information beyond optional language background. Do not collect names unless required for consent tracking. If collecting gameplay logs later, use a separate consent notice and anonymize user identifiers.

