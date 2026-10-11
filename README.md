# ATLAS — Enterprise AI Knowledge Assistant

ATLAS is a document based knowledge assistant. Users can search shared documents and ask questions with citations; administrators can upload and manage documents. Chat history is stored per user, and answers can stream from a local Ollama model.

## Stack and features

- **Backend:** Python 3.10, FastAPI, SQLAlchemy, Alembic, PostgreSQL 18 with pgvector.
- **AI:** multilingual E5 embeddings through Sentence Transformers, retrieval augmented generation, Ollama/Qwen3 streaming, source citations.
- **Frontend:** React, TypeScript, Vite and Nginx in Docker Compose.
- **Security:** JWT authentication, role and ownership checks, upload validation and resource limits.

The Docker Compose configuration runs PostgreSQL and the application in containers. Ollama runs on the host and is reached from the backend through `host.docker.internal`.

## Requirements

- Docker Desktop with Compose for the container setup.
- An Ollama service on the Windows host with the Qwen3 model configured by the application. The host service must accept requests from the backend container.
- For a manual setup: Python 3.10, Node.js 22, PostgreSQL 18 with the `vector` extension, and Ollama.

## Docker Compose

Create a local `.env.compose` in the project root with your own strong values:

```dotenv
ATLAS_DB_PASSWORD=replace_with_a_unique_database_password
JWT_SECRET_KEY=replace_with_a_long_random_jwt_secret
```

Do not commit this file. Start the application with:

```powershell
docker compose --env-file .env.compose up --build -d
```

The frontend is available at `http://127.0.0.1:8088`. Nginx proxies `/api/` to the backend on the same origin. PostgreSQL is available only inside the Compose network. The named volumes keep database records, uploads and the model cache across restarts.

## Manual local setup

Create a PostgreSQL database and user for ATLAS, and enable the `vector` extension. Copy [`backend/.env.example`](backend/.env.example) to `backend/.env`, then set your own database credentials and JWT secret. Keep that file local. Start Ollama and ensure the configured Qwen3 model is available.

```powershell
py -3.10 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt
Set-Location backend
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m uvicorn app.main:app --reload
```

In another terminal, from the project root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite uses `http://127.0.0.1:8000` as the API URL by default. The backend allows the local Vite development origins through CORS.

## Tests and CI

From `backend`, run `python -m pytest -q test`. From `frontend`, run `npm test`, `npm run build`, and `npm run lint`.

The [GitHub Actions workflow](.github/workflows/ci.yml) runs on pushes and pull requests to `main` and can be started manually. Its backend job uses an isolated PostgreSQL/pgvector service, applies Alembic migrations, verifies the schema and runs pytest. Its frontend job runs Vitest, ESLint and the production TypeScript build. Standard CI uses mocked Ollama and embedding behavior in tests; a real Qwen3 integration check requires the local Ollama setup.
