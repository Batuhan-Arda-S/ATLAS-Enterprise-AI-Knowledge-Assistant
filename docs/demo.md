# Synthetic ATLAS demo scenario

This is a reproducible scenario for a human reviewer. The same core flow was completed in an isolated managed Chromium context by the [automated browser acceptance test](../frontend/e2e/atlas-browser.e2e.mjs), with real screenshots in [assets](assets). The test uses the live Compose API and host Ollama; see [validation.md](validation.md) for results.

To repeat the automated acceptance run, start Compose and Ollama, then from `frontend` run `npx playwright install chromium` (first run only) and `npm run test:e2e`. It creates a fresh synthetic account and document each time. The test uses Playwright's browser `filechooser` event with a real TXT fixture path, not an API upload shortcut.

## Prepare fictional data

Start the local Compose stack and host Ollama as described in the [README](../README.md). From the repository root, create a fresh synthetic admin and nine-chunk fictional policy:

```powershell
python backend/scripts/evaluate_final.py --credentials-out "$env:TEMP\atlas-final-demo-credentials.json"
```

This command also runs the small RAG evaluation and writes `docs/evaluation-results.json`; it **adds** a synthetic account and document to the Docker database. Read the temporary credentials file locally for the browser login. Do not copy it to the repository, a screenshot or a shared message. Delete it after the demo.

## Browser walkthrough to verify manually

1. Open `http://127.0.0.1:8088` at a desktop viewport. Sign in using the synthetic credentials. Check that the Workspace, library and empty chat appear.
2. Open **Upload document** in the library. Enter title `ATLAS Synthetic Browser Upload` and department `Synthetic Evaluation`.
3. Use the browser's **File** control to select `backend/evaluation_data/final_policy.txt`. Submit; verify that the new document is selected and processed.
4. Ask: “What must staff do when a company laptop stops working?” Wait for visible incremental text, a completed response and a source link.
5. Open the source link. Confirm that Evidence Viewer shows the synthetic Devices passage and that the answer can be checked against it. An overlap highlight is only a reading aid.
6. Ask a follow-up: “How quickly will they acknowledge it?” Check the one-business-day answer and its source. Select the recent conversation again to verify history.
7. Use **New chat**, select the synthetic document if necessary and ask: “What is the maternity leave duration?” A supported response is abstention, because the policy does not provide that fact.
8. At a mobile-width viewport, open the library menu and Sources panel; inspect layout and interaction. Sign out and confirm that the login screen returns.

The committed screenshots show only a synthetic `@example.com` account and fictional policy content. Browser chrome, tokens, real addresses and private documents are absent. No video was produced.
