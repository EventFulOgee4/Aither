# Reliability and usability improvements

- Resolved nested merge conflicts in chat views and the model engine, retaining Anthropic, local Hugging Face, and OpenAI-compatible provider paths.
- Deferred retrieval-model imports until retrieval is needed; forwarded the selected tone to streaming generation.
- Added stream request validation, message length limits, session ownership validation, and mood intensity bounds.
- Added explicit stream failure events and atomic counter increments; removed raw user-message logging.
- Loaded every page of conversations and messages instead of stopping at 20 records.
- Replaced the undeclared Axios dependency with native fetch; shared concurrent token refreshes and preserved credentials during network outages.
- Restored drafts on stream errors, exposed inline errors/loading states, and guarded against stale session loads and navigation during sends.
- Fixed mood values, session linking, premature success feedback, and timer cleanup.
- Escaped titles in both print exports, handled blocked pop-ups, and improved keyboard focus, IME entry, accessible labels, and reduced-motion support.

## Verification

Frontend: `npm test`, `npm run lint`, `npm run build`.

Backend: `python manage.py test --settings=aitherapist.test_settings` from `backend`. Test settings use an in-memory SQLite database and do not need production database credentials or model downloads.

The regression suite covers ownership, authentication, input validation, mood logging, chat persistence, stream errors/tone, engine initialization, pagination, token refresh, and fragmented UTF-8 streams.

Live model responses, PostgreSQL connectivity, and visual browser behavior require a configured local environment and have not been verified by these automated checks. No database migrations are required by this change.

## Configuration

Set `VITE_API_BASE_URL` before building the frontend to override `http://127.0.0.1:8000/api`.

The model provider defaults to `anthropic` and requires `ANTHROPIC_API_KEY`. `AITHER_MODEL_NAME` overrides its model. Alternate providers are `openai_compatible` (requires `AITHER_MODEL_API_URL`; optional `AITHER_MODEL_API_KEY`) and `local_hf` (uses `AITHER_HF_MODEL`). Local dependencies are imported only when used; retrieval dependencies remain optional for responses that can proceed without retrieval.
