# Repository & Tool Feedback

**Tool:** PwC Delivery Launchpad
**Reviewed:** 2026-02-21

---

## Summary

The Delivery Launchpad is a well-conceived, standalone client-side tool that guides users through a structured AI-assisted engagement planning workflow. The overall UX, data model, and prompt architecture are solid. The feedback below is organised into **bugs** (things that are broken today), **UX issues**, and **code quality / maintainability** observations.

---

## Bugs

### 1. Invalid CSS — double `##` on background colours (3 occurrences)

**Files:** `index.html` lines 70, 257, 261

```css
/* Current (broken) */
background: ##F4F4F6;
background: linear-gradient(to right, ##F4F4F6, transparent);
background: linear-gradient(to left,  ##F4F4F6, transparent);

/* Should be */
background: #F4F4F6;
```

`##F4F4F6` is invalid CSS. Browsers silently ignore the rule, so the landing page background and the conveyor-belt edge-fade gradients render incorrectly (transparent instead of the intended light grey).

---

### 2. Stray closing brace inside the `<style>` block breaks header styles

**File:** `index.html` line 62

```css
    .header-subtitle { font-size: 13px; color: var(--secondaryText); font-weight: 400; }
    }          /* ← this closes the <style> block prematurely */

/* ─── LANDING PAGE ─── */
```

The extra `}` terminates the stylesheet early. All CSS that follows this line is parsed outside the `<style>` tag and is ignored, meaning the landing page, conveyor belt, guidance panel, and all other styles below the header block are not applied.

---

### 3. Guided-experience button labels include a trailing semicolon

**File:** `index.html` line 2446

```js
let nextLabel = isLast ? 'Finish;' : (isGoToWorkflow ? 'Go to Workflow;' : 'Next;');
```

All three button labels have a literal `;` appended. Users see **"Next;"**, **"Go to Workflow;"**, and **"Finish;"** in the UI. Remove the semicolons.

---

### 4. Stage-gate indicator never renders — wrong field name

**File:** `index.html` line 1834

```js
${prompt.stage_gate ? `<div class="Stage-gate">Stage gate</div>` : ''}
```

`workflow.json` uses the field name `sign_off_gate`, not `stage_gate`. Because `prompt.stage_gate` is always `undefined`, the Stage Gate badge is never shown for P1.5 (Engagement Charter) or P2.13 (PMO Playbook) even though both are flagged as sign-off gates in the data.

Fix: change the check to `prompt.sign_off_gate`.

---

### 5. Engagement data is only injected into P1.1 — all later prompts omit context

**File:** `index.html` lines 1883–1891 (`buildPromptText`)

```js
function buildPromptText(prompt, promptJson, data) {
  if (prompt.prompt_id === 'P1.1') {
    const briefJson = JSON.stringify(data, null, 2);
    const instruction = promptJson.instruction || '...';
    return instruction.replace('{{ENGAGEMENT_DATA}}', briefJson);
  }
  // All other prompts: return the template verbatim — no engagement data
  const instruction = promptJson.instruction || '...';
  return instruction;
}
```

P1.2 through P2.13 receive no engagement context from the brief builder. The tool relies entirely on the AI retaining memory across a long conversation, which is fragile (context windows, new sessions, model updates). At a minimum, a compact context block (client name, engagement name, industry, objectives) should be prepended to every prompt so each step is self-contained.

---

## UX Issues

### 6. No state persistence — all progress lost on page refresh

There is no use of `localStorage` or `sessionStorage`. If the user refreshes the browser mid-workflow, the form data, completed steps, and unlocked cards all reset. The UI acknowledges this ("Export saves a .txt backup, useful if your browser refreshes…") but the tool could silently auto-save state to `localStorage` and restore it on load with no user effort required.

---

### 7. No input validation on required fields

`client_name` and `engagement_name` are silently left as empty strings if not filled in. The prompt for P1.1 requires at minimum `client_name`, `engagement_name`, `industry`, and one objective, but there is no form-level validation or user-facing warning before the workflow can be started.

---

### 8. Tool requires a web server but gives no guidance on this

The `fetch()` calls for `./data/*.json` and `./prompts/*.json` will fail with a CORS/file:// error if a user simply double-clicks `index.html` to open it. There is no in-UI message or README explaining that the tool must be served over HTTP.

---

## Code Quality / Maintainability

### 9. No README

The repository has no `README.md`. There is no explanation of:
- What the tool does
- How to run it locally (e.g. `npx serve .` or `python -m http.server`)
- How to add or edit prompts
- How to update the reference data files

This is the single highest-leverage improvement for onboarding new contributors or users.

---

### 10. All HTML, CSS, and JavaScript in one 2,500-line file

`index.html` contains the entire application. Splitting it into `index.html`, `styles.css`, and `app.js` (and optionally separate modules for the form, workflow, and guided experience) would make the codebase significantly easier to navigate, debug, and extend.

---

### 11. Inconsistent brand orange — three different hex values in use

| Value | Location |
|---|---|
| `#FD5108` | CSS custom properties (`--orange500`) |
| `#E8530E` | Landing page badge, hover states, gradient backgrounds |
| `#D04A02` | PwC formatting standard in all prompt templates |

The UI and the generated documents will not match PwC brand guidelines. Standardise on one value (the prompt templates use `#D04A02`, which appears to be the correct PwC orange) and reference it via the CSS custom property.

---

### 12. CSS custom properties defined but not consistently used

`--orange500`, `--orange300`, `--orange100` etc. are defined in `:root` but large sections of CSS use hard-coded hex values instead. This makes theming and brand updates unnecessarily manual.

---

### 13. `#lp-grid` is defined but intentionally hidden with `display: none`

```css
#lp-grid { display: none; }
```

If the dot-grid background was removed from the design, the element and its CSS should be removed rather than hidden. Dead code adds noise.

---

## Prompt Architecture Observations

The prompts are well-structured and the PwC formatting standards section is thorough. A few observations:

- **`{{ENGAGEMENT_DATA}}` is only used in P1.1.** Consider whether a lightweight context block (5–10 key fields) should be injected into every prompt to make each step independently runnable.
- **Prompt files are plain JSON with a single `instruction` key.** A `version` field and a `last_updated` date would help track prompt evolution over time.
- **The `workflow.json` dependency graph is clean and correct.** P2.13 (PMO Playbook) correctly depends on all preceding P2 steps. No circular dependencies.
