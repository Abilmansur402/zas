# Hugging Face Space image (the backend only). The frontend is deployed to Vercel.
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Vectors: download → strip inflected forms → build the numpy cache → drop the
# text files. One RUN keeps the 600 MB download out of the final image, and the
# layer is reused as long as these files don't change (the cleaning keeps the
# daily words as roots, so editing words.py rebuilds it).
COPY scripts/clean_vocab.py backend/embeddings.py backend/morph.py backend/words.py ./
RUN mkdir -p data \
    && wget -q -O data/wiki.kk.vec https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.kk.vec \
    && python3 clean_vocab.py \
    && rm data/wiki.kk.vec \
    && VECTORS_PATH=data/wiki.kk.clean.vec CACHE_PATH=data/kk_vectors.npz \
       python3 -c "import embeddings as e; e.engine._load_sync()" \
    && rm data/wiki.kk.clean.vec clean_vocab.py

COPY backend/main.py backend/words.py backend/hints.py backend/embeddings.py backend/morph.py ./

ENV VECTORS_PATH=/app/data/wiki.kk.clean.vec \
    CACHE_PATH=/app/data/kk_vectors.npz \
    ALLOW_DUMMY_VECTORS=0 \
    ALLOWED_ORIGINS=https://zhasyrynsoz.vercel.app \
    DAY_UTC_OFFSET_HOURS=5
# SECRET_KEY: set it in the Space settings → Variables and secrets.

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers"]
