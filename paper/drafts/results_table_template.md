# Results Table Template

Use this table once human annotations and model scores are available.

| Model | Vocabulary size | Spearman rho | Pearson r | Notes |
|---|---:|---:|---:|---|
| FastText wiki.kk | TBD | TBD | TBD | Current baseline |
| FastText cc.kk.300 | TBD | TBD | TBD | Larger Common Crawl baseline |
| multilingual-e5-base | TBD | TBD | TBD | Transformer sentence encoder |
| BAAI bge-m3 | TBD | TBD | TBD | Multilingual transformer encoder |
| kaz-embedder | TBD | TBD | TBD | Kazakh-focused candidate |

## Error Categories

| Error category | Description | Example pair or neighbor | Model affected |
|---|---|---|---|
| Morphology | Model overweights inflected or derived forms | TBD | TBD |
| Loanwords | Russian or international loanwords distort similarity | TBD | TBD |
| Topical association | Words are associated but not semantically similar | TBD | TBD |
| Polysemy | One word has several senses and the model chooses a different one | TBD | TBD |
| Noise artifact | Vocabulary contains malformed or non-lemma item | TBD | TBD |

