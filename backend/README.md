# Backend model integration

Aither routes chat generation through `backend/ml/brain.py`.

## Database and startup

SQLite is the default. It stores data in `backend/db.sqlite3` and does not
require a PostgreSQL server or `DB_NAME`, `DB_USER`, and `DB_PASSWORD`.
Keep your existing `SECRET_KEY` in `backend/.env`. To explicitly select SQLite,
set `DB_ENGINE=sqlite` in that file.

After pulling these changes, run from the `backend` directory:

```bash
python manage.py migrate
python manage.py runserver
```

A new SQLite database starts with no accounts or chat history. Existing
PostgreSQL data is not transferred automatically. Do not commit `db.sqlite3`.

To use PostgreSQL later, set `DB_ENGINE=postgresql` and configure `DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` for a running server.

## Supported providers

### Anthropic (default)

Set `ANTHROPIC_API_KEY` and optionally `AITHER_MODEL_NAME`.

### 1) Local Hugging Face model

```bash
AITHER_MODEL_PROVIDER=local_hf
AITHER_HF_MODEL=microsoft/DialoGPT-medium
```

### 2) OpenAI-compatible API endpoint

```bash
AITHER_MODEL_PROVIDER=openai_compatible
AITHER_MODEL_API_URL=https://api.openai.com/v1/chat/completions
AITHER_MODEL_API_KEY=your_api_key
AITHER_MODEL_NAME=gpt-4o-mini
AITHER_MODEL_TIMEOUT_S=30
```

## Notes

- The frontend should not call model APIs directly.
- Requests should go through `/api/chat/messages/` or `/api/chat/stream/` so authentication, safety checks, session logging, and fallback behavior are preserved.
- If the model call fails, backend falls back to a safe default response.
