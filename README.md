# Delivery Launcher

Single-page workflow tool for capturing engagement context and generating sequenced planning prompts for delivery teams.

## Run locally

Because the app uses a large inlined payload in `index.html`, you can open it directly in a browser or serve it with any static server.

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Repository layout

- `index.html`: UI, styles, workflow rendering logic, and inlined data/prompts.
- `data/`: source JSON data used to build inlined payloads.
- `prompts/`: prompt templates by workflow step.
- `scripts/update_prompts.py`: maintenance script for bulk prompt updates.

## Prompt/data maintenance workflow

1. Update prompt JSON files in `prompts/` and/or data files in `data/`.
2. Run the prompt update helper when needed:
   ```bash
   python scripts/update_prompts.py
   ```
3. Validate JSON changes:
   ```bash
   python -m json.tool data/workflow.json >/dev/null
   python -m json.tool prompts/engagement_intake.json >/dev/null
   ```
4. Open the app and verify workflow cards render and prompt text is populated.

## Generated artifacts

From the workflow page, each step supports:

- Copy prompt text to clipboard.
- Export prompt text to `.txt`.
- Mark step complete to unlock dependent steps.

## Contribution and testing guidance

Before opening a PR:

- Run lightweight checks:
  - `python scripts/update_prompts.py` (should execute without path errors)
  - `python -m py_compile scripts/update_prompts.py`
- Smoke-test in browser:
  - Required fields block workflow start when empty.
  - Workflow starts successfully when required fields are provided.
  - Prompt cards include engagement context snapshot.
