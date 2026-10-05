# Жасырын Сөз

## Abstract

Kazakh remains underrepresented in resources for evaluating lexical semantic similarity. We present Жасырын Сөз, a Kazakh semantic word-guessing game and evaluation testbed for word-level embeddings. The system uses a curated vocabulary and ranks guesses by cosine similarity to a hidden target word. We use the game vocabulary to construct a native-speaker word-pair similarity dataset and compare static and transformer-based embedding models for Kazakh. The study evaluates how closely model similarities align with human judgments and analyzes common failure cases involving morphology, loanwords, topical association, and polysemy.

## 1 Introduction

Semantic word-guessing games such as Semantle and Contexto make distributional similarity visible to non-specialist users. A player submits guesses for a hidden word and receives feedback based on semantic closeness. This interaction is also useful for research: if a model ranks words in ways that feel unintuitive to speakers, the game exposes the mismatch immediately.

For Kazakh, this setting is especially useful because word-level lexical semantic resources are limited. Жасырын Сөз provides a practical environment for evaluating whether available embedding models capture similarity in a way that agrees with native-speaker intuition.

## 2 Related Work

This section will cover semantic guessing games, static word embeddings, multilingual sentence encoders, Kazakh NLP resources, and lexical similarity datasets such as SimLex and Multi-SimLex.

## 3 System Description

Жасырын Сөз is a web game with a React frontend and FastAPI backend. The backend stores a hidden target word and compares user guesses with the target using vector similarity. The frontend shows guess ranks, progress indicators, hints, and game history.

## 4 Vocabulary and Annotation Dataset

The initial vocabulary comes from manually grouped Kazakh word categories in the game repository. For the paper, the vocabulary is divided into a curated core and a noisy candidate block. Only clean curated items are used for the first annotation study.

## 5 Embedding Models

The planned comparison includes FastText models and multilingual transformer encoders. Transformer embeddings are precomputed offline for the vocabulary so the game server can use the same cosine-similarity ranking interface across models.

## 6 Evaluation Method

Native speakers rate word pairs on a 0-10 semantic similarity scale. Model cosine similarities are compared with mean human scores using Spearman and Pearson correlation. A second evaluation inspects top nearest neighbors for selected target words.

## 7 Results

To be filled after annotation and model evaluation.

## 8 Error Analysis

The analysis will group errors by morphology, loanwords, topical association, named entities or artifacts, and polysemy.

## 9 Limitations and Ethics

The first dataset is expected to be small. Gameplay logs, if used, require consent, anonymization, and clear exclusion of personally identifying information.

## 10 Conclusion

Жасырын Сөз demonstrates how an interactive game can support evaluation of Kazakh lexical semantic models while also producing reusable vocabulary and annotation resources.

