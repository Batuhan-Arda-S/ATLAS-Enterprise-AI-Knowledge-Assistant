# ATLAS local operations

Run the PowerShell commands from the repository root. The deployment binds its frontend to `127.0.0.1:8088`; the backend and PostgreSQL have no published host ports. The backend reaches Windows Ollama through `host.docker.internal:11434`. Do not expose Ollama or the frontend to the public internet without a separate deployment review.

## First setup and start

Install Docker Desktop with Compose and start the Windows Ollama service. Pull the configured `qwen3:4b-instruct` model in Ollama. Create a local `.env.compose` with your own strong `ATLAS_DB_PASSWORD` and `JWT_SECRET_KEY`; see the root README for placeholder syntax. Never commit that file.

On a new, empty ATLAS database:

```powershell
docker compose --env-file .env.compose build backend frontend
docker compose --env-file .env.compose up -d db
docker compose --env-file .env.compose run --rm backend alembic upgrade head
docker compose --env-file .env.compose up -d
```

For an existing installation, take a backup before applying new migrations. Check the current and expected revisions first:

```powershell
docker compose --env-file .env.compose exec -T backend alembic current
docker compose --env-file .env.compose exec -T backend alembic heads
.\scripts\backup.ps1
docker compose --env-file .env.compose exec -T backend alembic upgrade head
docker compose --env-file .env.compose up -d --build
```

Apply migrations only after reviewing them. Do not use `alembic stamp` to pretend that a migration ran. `docker compose up -d --build` keeps named volumes; never use `down -v` on the live installation.

## Health and diagnostics

```powershell
.\scripts\diagnostics.ps1
Invoke-RestMethod http://127.0.0.1:8088/api/health/live
Invoke-RestMethod http://127.0.0.1:8088/api/health/ready
Invoke-RestMethod http://127.0.0.1:8088/api/health/ollama
docker compose --env-file .env.compose ps
```

`live` checks the FastAPI process. `ready` checks PostgreSQL and the current Alembic head. `ollama` checks the configured local model separately; its failure does not trigger a backend restart. Docker marks the backend healthy from `ready` and the frontend healthy from its local Nginx response. A failed Docker healthcheck reports state; it does not itself restart a container. The `unless-stopped` policy restarts a process that exits unexpectedly or after Docker restarts, while honoring an explicit stop.

To inspect recent logs without dumping the whole history:

```powershell
docker compose --env-file .env.compose logs --tail 100 backend
docker compose --env-file .env.compose logs --tail 100 db
docker compose --env-file .env.compose logs --tail 100 frontend
```

Container logs rotate at 10 MB with three files per service. Backend error logs include an error type and operation, not request bodies, document contents or exception text. Treat logs as private operational data anyway.

## Backup and recovery verification

Pause uploads and other writes while taking a consistent database and storage snapshot. The backup script writes the PostgreSQL custom-format dump **inside the database container**, then uses `docker cp` to copy it to `%LOCALAPPDATA%\ATLAS\Backups` on Windows. It separately copies the upload volume from the backend and records SHA-256 hashes, migration revision and table counts. It never redirects binary `pg_dump` output through PowerShell.

```powershell
.\scripts\backup.ps1
.\scripts\verify-restore.ps1 -BackupDirectory 'C:\Users\<you>\AppData\Local\ATLAS\Backups\atlas-...'
```

Use the actual folder printed by the backup script. The restore check validates hashes and restores into a temporary PostgreSQL/pgvector container with no network or published port. It compares five table counts and the migration revision, then removes only that temporary container. It does **not** restore into `atlas_compose_db` or touch the Windows `enterprise_ai_db` database. Keep copies of the database dump **and** the `storage` directory together; a database dump alone cannot recover uploaded files. Protect backups with Windows account permissions and encrypted storage, and test restores regularly. Restoring into the live deployment requires a separate maintenance plan and explicit approval.

## Restart and stop

```powershell
docker compose --env-file .env.compose restart backend frontend
.\scripts\diagnostics.ps1
docker compose --env-file .env.compose stop
```

`stop` preserves the PostgreSQL, upload and model-cache volumes. For an application update, take a backup and run `docker compose --env-file .env.compose up -d --build` after any required migration.

## Common problems

- **PostgreSQL unavailable:** Check `docker compose --env-file .env.compose ps` and the recent `db` logs. Wait for its existing `pg_isready` healthcheck. If `ready` remains HTTP 503 after the database is healthy, compare `alembic current` with `alembic heads`; do not reset the database.
- **Ollama unavailable:** Check the Windows Ollama process and `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:11434/api/tags`. Confirm `qwen3:4b-instruct` is installed and the backend can reach `host.docker.internal:11434`. The backend readiness should still work when Ollama is down.
- **Disk nearly full:** Run `docker system df` and inspect backup storage plus the `atlas_atlas_hf_cache` volume. Keep the upload and PostgreSQL volumes. Remove old backups or model-cache data only after checking retention and recovery needs.
