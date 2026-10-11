# Final validation record — 11 October 2026

This is an evidence log for the private local ATLAS deployment. Tests used synthetic accounts/documents and the Docker Compose database; the separate Windows PostgreSQL database was not used. No live Docker volume was deleted. The final browser acceptance was completed after the initial Lesson 132 documentation commit.

## Baseline and automated checks

Before edits, the local `main` checkout matched `origin/main` and had no working-tree changes. Compose `db`, `backend` and `frontend` were running and healthy. Existing CI at the prior Lesson 131 commit was green; the Lesson 132 and final browser acceptance CI results are recorded below.

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
| Playwright Chromium browser acceptance | `npm run test:e2e` from `frontend`, live Compose API and host Ollama | **1 passed**; ten real screenshots |

The first pytest attempt was launched from the repository root and failed to import `app`; the same suite passed when run from its documented `backend` working directory. No test was skipped or weakened.

## Real Compose / Qwen3 integration

`backend/scripts/compose_e2e.py` ran against `http://127.0.0.1:8088/api` using a newly generated `@example.com` admin and fictional documents. It passed registration/login, a token-free 401 check, malformed PDF rejection, denied CORS origin, TXT upload and processed status, document listing, an injected-passage boundary check, conversation creation, an overlong-question rejection, real Qwen3 SSE, cited source loading, history and restart persistence. The stream emitted **24 token events** before `done`; the first-to-done gap was **0.41 seconds**. The script restarted only the existing Docker `db` and `backend` services, then confirmed the same history and document persisted. It did not remove volumes.

The 24-case synthetic RAG evaluation ran against the same Compose origin and real local Qwen3; see [evaluation.md](evaluation.md). That run created another synthetic admin and nine-chunk document. These tests prove the checked local API path, not every browser interaction or production environment.

## Backup and restore

The existing Lesson 131 backup `atlas-20261011-195702-c68a4a09` was verified again with `scripts/verify-restore.ps1`. The script checked the archive and upload SHA-256 hashes, restored into a temporary **network-isolated PostgreSQL container**, compared five table counts and the Alembic revision, then removed that temporary container. Result: **pass**. This proves that snapshot's consistency; it is not a fresh backup of records added during Lesson 132. No live restore was attempted.

## Browser acceptance and visual artifacts

The earlier Windows Computer Use attempt was blocked because it could not verify the open Edge URL. The final run instead used a **fresh Playwright-managed Chromium headless browser context** and the live `http://127.0.0.1:8088` application. No network route or API response was mocked. The full managed Chrome binary initially failed to launch on this Windows host because of a side-by-side configuration error; Playwright's managed Chromium headless shell launched successfully. The failed attempt was an environment launch issue, not an application test pass.

`frontend/e2e/atlas-browser.e2e.mjs` registered a random synthetic `@example.com` user, promoted only that account in the asserted `atlas_compose_db`, and logged in through the real React form. It opened the browser `filechooser` event and supplied the on-disk English TXT fixture, then verified HTTP 201, `processed` status, library listing and selection. It clicked **New chat**, sent an English question, observed nonempty assistant text while the UI still showed its pending state, and captured that screen **before** SSE `done`. It also read the real `text/event-stream` response and confirmed token frames preceded `done`; the successful final run had **62 token events**. It clicked the citation, checked that the returned chunk and document IDs matched the uploaded document and that the actual passage contained the expected one-business-day fact. It reopened the conversation through **Recent chats**, checked history, opened mobile library and Evidence panels, then signed out and confirmed that a reload remained on the login screen.

Viewport checks passed at **1920 × 1080**, **1440 × 900** and **390 × 844**. Screenshot review exposed a genuine mobile overflow: the chat region measured `scrollWidth=409` with `clientWidth=390`, visibly clipping assistant text. A new assertion reproduced the failure; setting the assistant body width/max-width to 100% fixed it. The full browser test then passed, and the updated mobile screenshot shows wrapped text. Ten unaltered application screenshots are in [assets](assets); all visible account/document/question/answer content is English and synthetic. No video was produced. Each test run adds synthetic records; it deletes no existing data.

## GitHub and secrets

The GitHub CLI authenticated as `Batuhan-Arda-S` and reported `Batuhan-Arda-S/ATLAS-Enterprise-AI-Knowledge-Assistant` as **PRIVATE** before and after push. Gitleaks v8.30.1 scanned the staged diff with `git --staged --redact` (about 66 KB) and found **no leaks**. `.env.compose`, backend/frontend `.env` files, model cache and temporary demo credentials were not staged. The temporary synthetic credentials file was removed after the browser tool stopped.

The initial Lesson 132 implementation/documentation commit `cecf82a` was pushed to private `main`. Its [ATLAS CI run](https://github.com/Batuhan-Arda-S/ATLAS-Enterprise-AI-Knowledge-Assistant/actions/runs/38171091188) **passed** both Backend Tests and Frontend Tests. The later documentation commit `778f4fd` also [passed CI](https://github.com/Batuhan-Arda-S/ATLAS-Enterprise-AI-Knowledge-Assistant/actions/runs/38171240935).

The final browser acceptance commit `8bed7ad` was pushed to the same **PRIVATE** repository. A fresh staged Gitleaks scan of its source and documentation found no leaks, and `.env.compose` remained ignored. Its [ATLAS CI run](https://github.com/Batuhan-Arda-S/ATLAS-Enterprise-AI-Knowledge-Assistant/actions/runs/38172078259) **passed** both jobs: isolated pgvector setup, migration verification, pytest, Vitest, lint and production build. This CI runner does not have the Windows Ollama service; the live browser/Qwen3 result above was measured locally against the running Compose stack.
