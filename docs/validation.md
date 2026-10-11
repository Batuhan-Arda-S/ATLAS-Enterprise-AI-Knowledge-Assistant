# Final validation record — 11 October 2026

This is an evidence log for the private local ATLAS deployment. It reports completed checks and an outstanding browser check separately. Tests used synthetic accounts/documents and the Docker Compose database; the separate Windows PostgreSQL database was not used. No live Docker volume was deleted.

## Baseline and automated checks

Before edits, the local `main` checkout matched `origin/main` and had no working-tree changes. Compose `db`, `backend` and `frontend` were running and healthy. Existing CI at the prior Lesson 131 commit was green; the Lesson 132 commit's CI result is recorded below after push.

| Check | Command / observation | Result |
| --- | --- | --- |
| Backend pytest | From `backend`, `..\.venv\Scripts\python.exe -m pytest -q test` | **141 passed**, one Starlette/httpx deprecation warning |
| Frontend Vitest | `node .\node_modules\vitest\vitest.mjs run` from `frontend` | **34 passed** across 8 files |
| ESLint | `node .\node_modules\eslint\bin\eslint.js .` | Pass, exit 0 |
| TypeScript | `node .\node_modules\typescript\bin\tsc -b` | Pass, exit 0 |
| Vite production bundle | `node .\node_modules\vite\bin\vite.js build` | Pass, 29 modules transformed |
| Compose health | `docker compose --env-file .env.compose ps` | db, backend and frontend **healthy** |
| HTTP health | `/api/health/live`, `/api/health/ready`, `/api/health/ollama` | HTTP **200** each |
| Alembic | `docker compose --env-file .env.compose exec -T backend alembic current` | `c49f5e82a731 (head)` |
| Mermaid parser | Six diagrams in README/architecture parsed with Mermaid 12.1.0 | Pass |

The first pytest attempt was launched from the repository root and failed to import `app`; the same suite passed when run from its documented `backend` working directory. No test was skipped or weakened.

## Real Compose / Qwen3 integration

`backend/scripts/compose_e2e.py` ran against `http://127.0.0.1:8088/api` using a newly generated `@example.com` admin and fictional documents. It passed registration/login, a token-free 401 check, malformed PDF rejection, denied CORS origin, TXT upload and processed status, document listing, an injected-passage boundary check, conversation creation, an overlong-question rejection, real Qwen3 SSE, cited source loading, history and restart persistence. The stream emitted **24 token events** before `done`; the first-to-done gap was **0.41 seconds**. The script restarted only the existing Docker `db` and `backend` services, then confirmed the same history and document persisted. It did not remove volumes.

The 24-case synthetic RAG evaluation ran against the same Compose origin and real local Qwen3; see [evaluation.md](evaluation.md). That run created another synthetic admin and nine-chunk document. These tests prove the checked local API path, not every browser interaction or production environment.

## Backup and restore

The existing Lesson 131 backup `atlas-20261011-195702-c68a4a09` was verified again with `scripts/verify-restore.ps1`. The script checked the archive and upload SHA-256 hashes, restored into a temporary **network-isolated PostgreSQL container**, compared five table counts and the Alembic revision, then removed that temporary container. Result: **pass**. This proves that snapshot's consistency; it is not a fresh backup of records added during Lesson 132. No live restore was attempted.

## Browser acceptance and visual artifacts

**Blocked / not passed:** The Windows Computer Use tool stopped when it could not determine the current Edge URL with enough confidence. Therefore this delivery did not execute the actual browser file-picker upload, visual document selection, Evidence Viewer click-through, mobile layout, browser logout, screenshot capture or demo video. Frontend component tests and API E2E cover parts of those flows, but are not substitutes for a real browser acceptance result. A repeatable synthetic [browser demo procedure](demo.md) is provided. No screenshots or video were fabricated.

## GitHub and secrets

The GitHub CLI authenticated as `Batuhan-Arda-S` and reported `Batuhan-Arda-S/ATLAS-Enterprise-AI-Knowledge-Assistant` as **PRIVATE** before and after push. Gitleaks v8.30.1 scanned the staged diff with `git --staged --redact` (about 66 KB) and found **no leaks**. `.env.compose`, backend/frontend `.env` files, model cache and temporary demo credentials were not staged. The temporary synthetic credentials file was removed after the browser tool stopped.

The implementation/documentation commit `cecf82a` was pushed to private `main`. Its [ATLAS CI run](https://github.com/Batuhan-Arda-S/ATLAS-Enterprise-AI-Knowledge-Assistant/actions/runs/38171091188) **passed** both Backend Tests and Frontend Tests: isolated pgvector setup, migration verification, pytest, Vitest, lint and production build. This validation record was finalized in a later documentation commit; check that later run separately in GitHub Actions.
