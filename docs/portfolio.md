# ATLAS portfolio material

This is draft wording for AI/ML Engineer and Applied AI Engineer applications. Adjust first-person ownership to match the work you can personally explain and demonstrate. Development involved AI tooling, including Codex; the material describes a built integration and its verified behavior, not original foundation-model research.

## Project overview

**ATLAS — Enterprise AI Knowledge Assistant** is a local, document-scoped retrieval-augmented assistant. Administrators upload PDF, DOCX or TXT policies; the backend extracts text, creates E5 embeddings, retrieves pgvector passages and asks a local Qwen3 model to answer with inspectable citations. A React workspace streams answers, retains user-owned conversations and opens cited passages in an Evidence Viewer.

**Stack:** Python 3.10, FastAPI, SQLAlchemy, Alembic, PostgreSQL 18/pgvector, Sentence Transformers (`intfloat/multilingual-e5-small`), Ollama (`qwen3:4b-instruct`), React, TypeScript, Vite, Nginx, Docker Compose, pytest, Vitest and GitHub Actions.

## Engineering work to discuss

- Built an end-to-end document ingestion route with format validation, parser limits, chunking, embeddings and persistence.
- Scoped vector search to the selected document and kept conversation reads and streaming tied to the authenticated owner.
- Designed SSE completion/error handling, required citations from retrieved source IDs, and exposed source passages for manual checking.
- Added local deployment health gates, persistent volumes, backup and isolated restore verification, and separate backend/frontend CI jobs.
- Measured a 24-case synthetic RAG set with explicit expected facts and relevant chunks; reported answer and retrieval failures rather than claiming universal accuracy.

These bullets describe repository work. Before using them in a CV, the applicant should be ready to explain which parts they personally designed, implemented, reviewed or accepted with AI assistance.

## CV entry — short

**ATLAS | Applied AI / Full-stack RAG project** — Built and validated a local document-question-answering application using FastAPI, PostgreSQL/pgvector, multilingual E5, Ollama/Qwen3 and React. Implemented bounded uploads, document-scoped retrieval, SSE responses, citations, chat history, CI and operational checks. Final local verification: 141 backend tests and 34 frontend tests passed; a 24-case synthetic retrieval set yielded mean Recall@3 of 0.984 on 21 questions with predefined relevant sources (small-sample result, not production accuracy).

## CV entry — expanded

**ATLAS — Enterprise AI Knowledge Assistant**

- Integrated PDF/DOCX/TXT ingestion, 500-character smart chunking, 384-dimensional multilingual E5 embeddings and pgvector cosine retrieval in a FastAPI service backed by PostgreSQL and Alembic.
- Implemented document-scoped Qwen3 RAG with streamed SSE responses, source-ID citation checks and a React Evidence Viewer that loads full cited passages.
- Added JWT authentication, admin document operations, conversation ownership checks, parser and upload limits, non-root containers, same-origin Nginx proxying, health checks and backup/restore procedures.
- Maintained pytest/Vitest/ESLint/TypeScript gates and a GitHub Actions workflow. Evaluated a controlled synthetic corpus and documented both measured retrieval performance and an observed model abstention error.
- Used AI-assisted development and review tools, including Codex; verified behavior through code inspection, automated tests and local end-to-end runs.

## LinkedIn post draft

I completed ATLAS, a local retrieval-augmented knowledge assistant built as a full-stack AI engineering project. It accepts PDF, DOCX and TXT documents, stores multilingual E5 passage embeddings in PostgreSQL/pgvector, and uses Ollama/Qwen3 to stream document-grounded answers with source links. The React Evidence Viewer lets a reader inspect the cited passage instead of relying only on the generated answer.

The engineering work covered authentication and ownership boundaries, upload limits, Docker Compose deployment, health checks, backups, CI and a small reproducible synthetic evaluation. In that set, 21 answerable/relevant-source questions reached mean Recall@3 of 0.984; one of eight manually reviewed answer examples was too cautious on a contradiction question. These numbers describe this fixture only and do not establish production accuracy.

I used AI development assistance, including Codex, and checked the resulting system with tests and real local Qwen3/PostgreSQL runs. I can walk through the architecture, the measured limitations and the design trade-offs.

## Interview discussion prompts

1. **Why document-scoped retrieval?** The current product requires selecting one shared document. The SQL query filters `document_id` before vector ranking, making the boundary clear and testable. A cross-document assistant would need a separate access policy and evaluation design.
2. **What does citation validation guarantee?** It rejects IDs outside the retrieved set; it does not prove semantic entailment. The Evidence Viewer is deliberately a human verification surface.
3. **How does multi-turn work?** The backend uses the most recent prior user question to expand the search query and includes recent conversation messages in the model prompt. History is stored under the authenticated conversation owner.
4. **Why separate CI and local acceptance?** CI runs deterministic tests with isolated pgvector. Real Qwen3 and host Ollama are checked locally because standard GitHub runners do not reproduce that environment.
5. **What would you improve next?** Add a documented sharing/ACL model, queue and isolate ingestion, rate limits, model/evaluation monitoring, and a larger human-labeled benchmark before broader deployment.
