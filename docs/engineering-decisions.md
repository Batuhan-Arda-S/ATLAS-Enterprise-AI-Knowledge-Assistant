# Engineering decisions and trade-offs

The implementation facts below are verified from the current repository. Where the development history does not record why a technology was originally selected, the rationale is explicitly a **retrospective engineering assessment**, not a claim about the author's original intent.

| Choice | Verified implementation | Retrospective assessment and cost |
| --- | --- | --- |
| FastAPI | Typed Pydantic schemas, dependency-based auth, sync and streaming routes in `backend/app/routers/` | Good fit for explicit API contracts and a Python retrieval stack. Synchronous parsing and embedding in an upload request can make long uploads slow; a job queue would be needed for larger workloads. |
| PostgreSQL + pgvector | SQLAlchemy models, Alembic migrations, 384-dimensional vectors and cosine search scoped by document ID | Keeps chat, document metadata and vectors in one transactional store. This simple topology avoids a separate vector service, but scaling and search tuning remain tied to PostgreSQL capacity. |
| Local Qwen3 | `qwen3:4b-instruct` through an Ollama HTTP endpoint | Local inference reduces dependence on a hosted model and makes the demo usable without a paid API. It requires a separately configured host Ollama service, model download, enough host resources and a trust decision about the host boundary. |
| Multilingual E5 small | `intfloat/multilingual-e5-small`, `query:`/`passage:` prefixes and 384-dimensional embeddings | Supports multilingual semantic retrieval with a relatively compact vector. The repository has a small synthetic evaluation, not evidence of broad production ranking quality; model changes would require re-embedding. |
| SSE | FastAPI `StreamingResponse`, `token`/`done`/`error` events, browser fetch reader | Fits one-way incremental answers over HTTP and Nginx same-origin proxying. It requires careful handling of partial failure and buffering; unsuccessful partial text is explicitly unverified in the UI. |
| Citation-driven Evidence Viewer | Retrieved source IDs checked server-side; `GET /documents/{id}/chunks/{chunk_id}` loads full passage; exact overlap optionally highlighted | Makes a source inspectable in context and gives users a route to challenge an answer. ID membership and text overlap cannot prove the cited passage supports every claim. |
| Docker Compose | Separate database, backend and frontend services, private network and persistent volumes | Reproducible local topology with straightforward health and backup operations. It is a single-host arrangement and does not supply high availability, public TLS termination or distributed scheduling. |
| Separate backend/frontend images | Python + model dependencies in backend; Vite build served by non-root Nginx in frontend | Keeps runtime concerns separate and allows same-origin `/api` routing. Two builds and a host Ollama dependency add setup steps. |
| No real GPU inference in CI | GitHub Actions runs isolated pgvector + pytest and frontend checks; model behavior is mocked | Avoids depending on runner GPU hardware or a Windows host Ollama service. Real-model smoke tests remain a separate local acceptance gate and are reported independently. |

## Deliberate current limits

- The corpus is shared among admins. There is no per-document owner, tenant, department ACL or employee read role. Expanding the product's sharing model requires a policy design and corresponding retrieval/citation tests.
- Retrieval selects the top `k` candidate chunks without an active similarity threshold. The model is asked to abstain when evidence is insufficient, but this is not a deterministic factuality filter.
- A citation must identify a retrieved chunk. Semantic support is reviewed by a human in the small final evaluation; it is not formally verified by the backend.
- Password login has a 30-minute access token by default and no refresh flow, password reset, MFA or rate limiting. The frontend keeps the token in memory, so a reload requires login again.
- Uploads are bounded by file, parser and extracted-text limits. Processing still happens in the request path and should be moved to an isolated worker before use with untrusted high-volume uploads.
- The GitHub repository is public, while this Compose setup remains loopback-only. Deploying the application to the public internet would require a separate threat model and operations design.
