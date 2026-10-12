---
title: Zhasyrynsoz
emoji: 🎮
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Жасырын Сөз

Қазақша мағыналық сөз ойыны (в духе Contexto / Semantle). Каждый день загадано одно
казахское существительное. Игрок вводит слова, а игра показывает, на каком месте
по смысловой близости к загаданному слову стоит каждая догадка. Место 1 означает,
что слово найдено.

- **Режимы:** слово дня, случайное слово, своё слово для друга (по ссылке).
- **Подсказки:** категория, первая буква, длина, далёкое/среднее/близкое слово.
- **Шаринг результата** в стиле Wordle и статистика в браузере.

**Стек:** FastAPI + NumPy (векторы FastText `wiki.kk`) · React + Vite.

## Структура

```
backend/      FastAPI: main.py (API), embeddings.py (ранжирование), words.py (слова дня), hints.py
frontend/     React-клиент
scripts/      скачивание и очистка векторов, подготовка списка слов
paper/        материалы статьи
Dockerfile    образ для Hugging Face Space (только бэкенд)
```

## Локальный запуск

**Быстро, без векторов** (сходство случайное, подходит только для работы над UI):

```bash
cd backend
cp .env.example .env            # там уже ALLOW_DUMMY_VECTORS=1
pip install -r requirements-dev.txt
uvicorn main:app --reload       # http://localhost:8000

cd ../frontend
npm ci && npm run dev           # http://localhost:3000, /api проксируется на :8000
```

**С настоящими векторами:**

```bash
./scripts/download_vectors.sh          # ~600 МБ → data/wiki.kk.vec
python3 scripts/clean_vocab.py         # → data/wiki.kk.clean.vec (без падежных форм)
# в backend/.env: VECTORS_PATH=../data/wiki.kk.clean.vec, ALLOW_DUMMY_VECTORS=0
```

При первом запуске бэкенд создаёт `data/kk_vectors.npz`, и дальнейшие запуски занимают
секунды. Кэш пересобирается сам, если `.vec` файл изменился.

**Всё в Docker:** `docker compose up --build` → http://localhost:8080
(векторы должны лежать в `./data`).

**Тесты:** `cd backend && pytest -q`. Они идут на тестовых векторах, скачивать ничего
не нужно. CI (GitHub Actions) запускает тесты и сборку фронтенда на каждый push и PR.

## Выпуск

### 1. Бэкенд → Hugging Face Space

1. Создайте Space с типом **Docker** (бесплатного CPU basic хватает).
2. В **Settings → Variables and secrets** добавьте:
   - `SECRET_KEY` (secret): длинная случайная строка,
     `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Ею подписываются
     ссылки на «своё слово». Если её поменять, старые ссылки перестанут работать.
   - `ALLOWED_ORIGINS` (variable): адрес фронтенда, например `https://zhasyrynsoz.vercel.app`.
3. Запушьте репозиторий в Space (`git remote add space https://huggingface.co/spaces/<user>/<space>`
   и `git push space main`). При сборке образ сам скачает и очистит векторы, а также
   соберёт кэш. Первая сборка занимает 10–15 минут.
   Если HF отклонит push из-за бинарных файлов (`.docx`, `.png`), уберите их из ветки
   для Space или включите для них Git LFS/Xet.
4. Проверка: `https://<user>-<space>.hf.space/health` должен вернуть `"dummy_vectors": false`
   и `daily_words` около 800. В логах Space видно, какие слова дня пропущены, потому что
   их нет в словаре векторов.

Бесплатный Space засыпает после ~48 часов без запросов. Первый запрос после сна ждёт
загрузку (около минуты), фронтенд в это время показывает «Сервер іске қосылып жатыр».

### 2. Фронтенд → Vercel

1. Import project → выберите репозиторий, **Root Directory = `frontend`**
   (Vite определится сам: `npm run build`, папка `dist`).
2. Environment Variables: `VITE_API_URL = https://<user>-<space>.hf.space`.
3. Deploy. После смены домена обновите `ALLOWED_ORIGINS` в Space.

### 3. Чек-лист перед анонсом

- [ ] `/health` без dummy-векторов, в логах нет ошибок
- [ ] Слово дня: угадывание, все 6 подсказок, победа, топ-60 похожих слов
- [ ] Случайная игра и «Өз сөзім»: ссылка открывается у друга в другом браузере
- [ ] Кнопка «Бөлісу» на телефоне (Telegram, WhatsApp)
- [ ] Превью ссылки в Telegram показывает картинку `og.png`
- [ ] Прогнать список слов: удалить слишком редкие и неоднозначные

## Настройки бэкенда

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VECTORS_PATH` | `./data/wiki.kk.clean.vec` | очищенные векторы FastText |
| `CACHE_PATH` | `./data/kk_vectors.npz` | numpy-кэш для быстрого старта |
| `ALLOW_DUMMY_VECTORS` | `0` | `1` = случайные векторы, если файла нет (только для разработки) |
| `SECRET_KEY` | — | подпись ссылок на свои игры |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | CORS |
| `DAY_UTC_OFFSET_HOURS` | `5` | слово дня меняется в полночь по времени Казахстана |
| `RANK_CACHE_SIZE` | `64` | сколько загаданных слов держать в памяти с готовыми рангами |

## API

| Метод | Путь | |
|---|---|---|
| GET | `/health` | статус, размер словаря |
| GET | `/api/daily` | `game_id` на сегодня |
| GET | `/api/random` | случайный `game_id` |
| POST | `/api/custom` `{word}` | токен своей игры |
| POST | `/api/guess` `{game_id \| custom_token, guess}` | ранг догадки |
| GET | `/api/hint/{game_id}?hint_type=&offset=` | подсказка (есть и `/api/hint/custom/{token}`) |
| GET | `/api/similar/{game_id}?word=<ответ>` | 200 ближайших слов, только если `word` верный |
