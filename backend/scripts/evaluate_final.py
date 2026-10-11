"""Run the small synthetic final evaluation against the local Compose origin.

Requires only Python's standard library and the running ATLAS Compose stack.
Creates a new synthetic admin and document; it never changes existing records.
"""

import argparse
import json
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "evaluation_data"
BASE = "http://127.0.0.1:8088/api"
COMPOSE = ["docker", "compose", "--env-file", ".env.compose"]


def api(method, path, payload=None, token=None, content_type="application/json"):
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None if payload is None else (
        json.dumps(payload).encode("utf-8") if content_type == "application/json" else payload
    )
    request = Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=180) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"{method} {path} returned HTTP {error.code}") from error


def upload_body(title, contents):
    boundary = "atlas" + secrets.token_hex(12)
    parts = []
    for key, value in (("title", title), ("department", "Synthetic Evaluation")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode())
    parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                  "filename=\"final_policy.txt\"\r\nContent-Type: text/plain\r\n\r\n").encode())
    parts.append(contents)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def promote(email):
    code = (
        "import sys; from sqlalchemy import text; from app.database.connection import engine; "
        "c=engine.connect(); t=c.begin(); "
        "assert c.execute(text('SELECT current_database()')).scalar_one()=='atlas_compose_db'; "
        "r=c.execute(text(\"UPDATE users SET role='admin' WHERE email=:email\"), {'email':sys.argv[1]}); "
        "assert r.rowcount==1; t.commit(); c.close()"
    )
    subprocess.run(COMPOSE + ["exec", "-T", "backend", "python", "-c", code, email],
                   cwd=ROOT, check=True, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "evaluation-results.json")
    parser.add_argument("--credentials-out", type=Path)
    args = parser.parse_args()

    dataset = json.loads((DATA / "final_cases.json").read_text(encoding="utf-8"))
    contents = (DATA / dataset["document"]).read_bytes()
    email = f"atlas-final-{uuid4().hex[:12]}@example.com"
    password = secrets.token_urlsafe(24)
    assert api("POST", "/users/register", {"email": email, "password": password})[0] == 201
    promote(email)
    token = api("POST", "/users/login", {"email": email, "password": password})[1]["access_token"]
    if args.credentials_out:
        args.credentials_out.parent.mkdir(parents=True, exist_ok=True)
        args.credentials_out.write_text(json.dumps({"email": email, "password": password}), encoding="utf-8")

    body, content_type = upload_body("ATLAS Synthetic Final Policy", contents)
    status, document = api("POST", "/documents/upload", body, token, content_type)
    assert status == 201 and document["processing_status"] == "processed", document
    document_id = document["id"]
    status, listing = api("POST", f"/documents/{document_id}/search",
                          {"question": "ATLAS synthetic policy", "limit": 10}, token)
    assert status == 200
    indexes = {hit["chunk_index"]: hit["chunk_id"] for hit in listing["results"]}
    assert set(indexes) == set(range(9)), f"Expected nine source chunks; got {sorted(indexes)}"
    print(f"Synthetic document processed: {len(indexes)} chunks", flush=True)

    rows = []
    for case in dataset["cases"]:
        prior = next((m["content"] for m in reversed(case.get("history", [])) if m["role"] == "user"), None)
        search_question = f"{prior}\n{case['question']}" if prior else case["question"]
        _, search = api("POST", f"/documents/{document_id}/search",
                        {"question": search_question, "limit": 3}, token)
        retrieved = [hit["chunk_index"] for hit in search["results"]]
        relevant = case["relevant_chunk_indexes"]
        row = {"id": case["id"], "type": case["type"], "question": case["question"],
               "expected": case["expected"], "relevant_chunk_indexes": relevant,
               "retrieved_chunk_indexes": retrieved,
               "recall_at_3": len(set(retrieved) & set(relevant)) / len(relevant) if relevant else None}
        rows.append(row)
        print(f"{case['id']}: retrieved {retrieved} recall={row['recall_at_3']}", flush=True)

    # A prespecified answer sample covers simple, cross-chunk, unknown, conflict and injection cases.
    answer_ids = {"q01", "q13", "q14", "q18", "q21", "q22", "q23", "q24"}
    reverse_indexes = {value: key for key, value in indexes.items()}
    for row in rows:
        if row["id"] not in answer_ids:
            continue
        try:
            _, answer = api("POST", "/ask", {"document_id": document_id,
                                               "question": row["question"], "limit": 3}, token)
            row["answer_status"] = answer["answer_status"]
            row["answer"] = answer["answer"]
            row["cited_chunk_indexes"] = [reverse_indexes[source["chunk_id"]]
                                          for source in answer["cited_sources"]]
            print(f"{row['id']}: answer_status={row['answer_status']}", flush=True)
        except RuntimeError as error:
            row["answer_error"] = str(error)
            print(f"{row['id']}: {error}", flush=True)

    measured = [row["recall_at_3"] for row in rows if row["recall_at_3"] is not None]
    result = {"dataset": dataset["dataset"], "measured_at_utc": datetime.now(timezone.utc).isoformat(),
              "model": "qwen3:4b-instruct", "embedding": "intfloat/multilingual-e5-small",
              "retrieval_k": 3, "retrieval_case_count": len(measured),
              "mean_recall_at_3": sum(measured) / len(measured),
              "unanswerable_case_count": len(rows) - len(measured),
              "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Mean Recall@3: {result['mean_recall_at_3']:.3f} across {len(measured)} cases", flush=True)
    print(f"Results: {args.output}", flush=True)


if __name__ == "__main__":
    main()
