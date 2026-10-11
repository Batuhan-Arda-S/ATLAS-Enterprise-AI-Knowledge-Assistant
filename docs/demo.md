# Synthetic ATLAS demo scenario

This is a **reproducible scenario**, not a claim that browser screenshots or a video were captured in Lesson 132. The local Computer Use tool stopped before browser interaction. The API-level Qwen3/SSE/citation path was verified independently in [validation.md](validation.md).

## Prepare fictional data

Start the local Compose stack and host Ollama as described in the [README](../README.md). From the repository root, create a fresh synthetic admin and nine-chunk fictional policy:

```powershell
python backend/scripts/evaluate_final.py --credentials-out "$env:TEMP\atlas-final-demo-credentials.json"
```

This command also runs the small RAG evaluation and writes `docs/evaluation-results.json`; it **adds** a synthetic account and document to the Docker database. Read the temporary credentials file locally for the browser login. Do not copy it to the repository, a screenshot or a shared message. Delete it after the demo.

## Browser walkthrough to verify manually

1. Open `http://127.0.0.1:8088` at a desktop viewport. Sign in using the synthetic credentials. Check that the Workspace, library and empty chat appear.
2. Open **Upload document** in the library. Enter title `ATLAS Synthetic Browser Upload` and department `Synthetic Evaluation`.
3. Use the browser's **File** control and the actual operating-system file picker to select `backend/evaluation_data/final_policy.txt`. Submit; verify that the new document is selected and processed. This specific file-picker action remains unverified in the final delivery.
4. Ask: “What must staff do when a company laptop stops working?” Wait for visible incremental text, a completed response and a source link.
5. Open the source link. Confirm that Evidence Viewer shows the synthetic Devices passage and that the answer can be checked against it. An overlap highlight is only a reading aid.
6. Ask a follow-up: “How quickly will they acknowledge it?” Check the one-business-day answer and its source. Select the recent conversation again to verify history.
7. Use **New chat**, select the synthetic document if necessary and ask: “What is the maternity leave duration?” A supported response is abstention, because the policy does not provide that fact.
8. At a mobile-width viewport, open the library menu and Sources panel; inspect layout and interaction. Sign out and confirm that the login screen returns.

For screenshots, capture only the synthetic account and fictional documents. Avoid browser chrome showing personal tabs, real email addresses, tokens or private files. A short optional video can follow the same sequence. No video was produced in this delivery.
