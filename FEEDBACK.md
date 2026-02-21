# Repository Review Feedback

**Tool:** PwC Delivery Launchpad  
**Reviewed:** 2026-02-21

---

## What is working well

- The product has a clear end-to-end workflow model (`P1` initiation and `P2` planning), with explicit dependency wiring and sign-off gates in `data/workflow.json`.
- Prompt templates are comprehensive and strongly formatted for structured outputs.
- The app can bootstrap entirely from inlined data (`INLINED_DATA` / `INLINED_PROMPTS`), which makes the UI resilient even when static file loading fails.

---

## High-priority issues

### 1) Prompt context is only injected for `P1.1`

`buildPromptText` only replaces `{{ENGAGEMENT_DATA}}` for `P1.1`, while all later steps return the prompt instruction unchanged. This makes downstream prompts heavily dependent on LLM conversation memory instead of deterministic context injection.

**Why it matters:** Later steps can drift, especially in long sessions or model/context resets.

**Recommendation:** Inject a compact context block into every prompt (at least client, engagement, industry, delivery methodology, fee model, key objectives), not only `P1.1`.

---

### 2) Required fields are visually marked but not validated before workflow start

`client_name` and `engagement_name` are marked required in the UI, but `collectFormData()` defaults missing values to empty strings and `startWorkflow()` proceeds.

**Why it matters:** Empty context fields degrade generated artifacts and can force avoidable clarification loops.

**Recommendation:** Add blocking validation for minimum required inputs with inline error states before starting the workflow.

---

### 3) Repository utility script targets the wrong absolute path

`scripts/update_prompts.py` sets:

```python
PROMPTS_DIR = '/home/user/delivery-launcher/prompts'
```

This is environment-specific and does not match this repository path (`/workspace/delivery-launcher`).

**Why it matters:** Script fails silently or exits with “directory does not exist” when run in other environments.

**Recommendation:** Resolve paths relative to the script file (e.g., `Path(__file__).resolve().parents[1] / 'prompts'`).

---

## Medium-priority improvements

### 4) Single-file architecture is hard to maintain

`index.html` contains all HTML/CSS/JS and very large inlined data payloads.

**Recommendation:** Split into `index.html`, `styles.css`, `app.js`, and optionally `data.js` modules. This improves readability, caching behavior, and change isolation.

---

### 5) No contributor/runbook documentation

There is no `README.md`.

**Recommendation:** Add a README covering:
- local run instructions,
- data/prompt update workflow,
- expected generated artifacts,
- contribution/testing guidance.

---

### 6) No persistence for in-progress planning sessions

No `localStorage`/`sessionStorage` save/restore flow exists.

**Recommendation:** Auto-save form/workflow state and restore on load. Keep export as a backup, not the primary recovery path.

---

## Suggested next steps

1. Implement required-field validation and per-step context injection.
2. Fix `scripts/update_prompts.py` path handling.
3. Add `README.md` with run + maintenance instructions.
4. Start modularizing UI code (CSS/JS extraction first).
5. Add lightweight persistence for user progress.

---

## Quick checks run during review

- `python -m json.tool data/workflow.json`
- `python -m json.tool prompts/engagement_intake.json`
- `python scripts/update_prompts.py` (fails due to hard-coded path; expected based on finding #3)
