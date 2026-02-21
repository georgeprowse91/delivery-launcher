#!/usr/bin/env python3
"""
Apply systematic improvements to all prompt JSON files.
Changes applied:
  1. Engagement Context Block prepended to every instruction (except engagement_intake)
  2. Thin-Context Warning inserted before STEP 1 (except engagement_intake)
  3. Excel Workbook Rationalisation directive inserted before the Excel section
  4. Fee Structure Branch added to budget_cost_baseline.json
  5. Methodology Branch added to schedule_milestones.json and critical_path.json
  6. Cross-Document Consistency Audit added to pmo_playbook.json
"""

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / 'prompts'

# Files that require NO changes (first step / already updated by agent)
SKIP_FILES = {
    'engagement_intake.json',
    'governance_framework.json',
    'work_breakdown_structure.json',
}

# ── 1. Engagement Context Block ──────────────────────────────────────────────

CONTEXT_BLOCK = """\
ENGAGEMENT CONTEXT — populate all fields before running this prompt. \
These values override anything inferred from prior steps.

Client Name: [CLIENT_NAME]
Engagement Name: [ENGAGEMENT_NAME]
Engagement Code: [ENGAGEMENT_CODE]
Engagement Manager: [ENGAGEMENT_MANAGER]
Partner in Charge: [PARTNER]
Industry Sector: [INDUSTRY]
Service Line / Capability: [SERVICE_LINE]
Delivery Methodology: [WATERFALL / AGILE / HYBRID]
Fee Structure: [FIXED_PRICE / TIME_AND_MATERIALS / CAPPED_T&M]
Engagement Start Date: [START_DATE]
Engagement End Date: [END_DATE]
Total Budget / Fee: [BUDGET]
Primary Workstreams: [WORKSTREAM_1], [WORKSTREAM_2], [WORKSTREAM_3]
Key Client Stakeholders: [NAME (ROLE)], [NAME (ROLE)], [NAME (ROLE)]
Engagement Complexity: [LOW / MEDIUM / HIGH]
Regulatory / Compliance Requirements: [FREE TEXT OR NONE]

---

"""

# ── 2. Thin-Context Warning (parameterised by artifact name) ─────────────────

def thin_context_warning(artifact):
    return f"""\
CONTEXT CHECK

Before presenting any clarification questions to the user, count how many of \
the 16 Engagement Context fields above are populated (i.e. not blank and not \
still containing a placeholder such as [CLIENT_NAME]).

If fewer than 8 of the 16 fields are completed, stop and output the message \
below — do not proceed to Step 1 until the user confirms the fields have been \
filled:

"⚠️ Insufficient engagement context detected. Only [N] of 16 required context \
fields are populated. To generate a meaningful {artifact} rather than a generic \
template, please fill in at minimum: Client Name, Engagement Name, Delivery \
Methodology, Fee Structure, Engagement Start Date, Total Budget, and Primary \
Workstreams. Update the context block above and re-run."

If 8 or more fields are populated, proceed to Step 1 below.

---

"""

# ── 3. Per-file Excel Rationalisation directives ─────────────────────────────

EXCEL_RATIONALISATIONS = {

    'objectives_benefits.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Objectives & Success Criteria Register — the primary data sheet combining \
objectives, KPIs, and success criteria in one table with columns for Objective, \
KPI / Metric, Baseline, Target, Measurement Method, Frequency, Owner, and \
Status.
2. Measurement Tracker — period-by-period progress against each KPI (merge any \
separate baseline / target sheets here).
3. Objectives RACI — ownership and accountability for each objective.
4. Change Log.
Do not generate separate archive or reference sheets.

""",

    'scope_statement.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Scope Register — inclusions, exclusions, and assumptions in one table with \
a clear "Type" column (Inclusion / Exclusion / Assumption / Constraint).
2. Scope Change Log — tracks scope changes against the agreed baseline; add a \
"Status" column (Pending / Approved / Rejected) and use filtering rather than \
a separate archive.
3. Scope RACI — ownership of scope elements by workstream.
4. Change Log.
Do not generate separate assumption register or archive sheets.

""",

    'stakeholder_analysis.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Stakeholder Register — full register with all columns (Name, Role, \
Organisation, Influence, Interest, Engagement Strategy, Owner, Notes).
2. Engagement Plan — planned engagement activities per stakeholder \
(Stakeholder | Activity | Frequency | Next Date | Owner | Status).
3. Stakeholder Heat Map — 2×2 influence/interest matrix populated from the \
register (use conditional formatting to colour-code quadrants).
4. Change Log.
Do not generate separate archive or communication preference sheets — fold \
preferences into the Stakeholder Register as columns.

""",

    'engagement_charter.json': """\
NOTE: The Engagement Charter produces a Word document only — no Excel workbook. \
If the existing prompt describes any Excel output, omit it.

""",

    'communications_plan.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Communications Matrix & Calendar — merge the full communications matrix \
with scheduling columns (Planned Date, Frequency, Next Due) in one table; \
add a "Confidential (Y/N)" column rather than a separate sensitive log.
2. Message Library — pre-built communication templates, kept as is.
3. Distribution Lists & Effectiveness — audience distribution lists at top, \
effectiveness tracking table (feedback and satisfaction) below with a clear \
section header.
4. Change Log.
Do not generate a separate Sensitive Communications Log or Communication \
Calendar sheet.

""",

    'critical_path.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets (or replace \
entirely with Sprint Dependency sheets if Agile — see methodology adaptation \
below):
1. Critical Path Analysis — include Float Analysis columns (Total Float, Free \
Float, Critical Y/N) directly on this sheet rather than a separate tab.
2. Dependency Network — include External Dependencies as a second table below \
the main network with a clear section header.
3. Fast-Track & Crash Analysis — include the Scenario Modeller in the lower \
half of this sheet (scenarios tested below the base analysis table).
4. Change Log.
Do not generate separate Float Analysis, External Dependencies Register, or \
Scenario Modeller sheets.

""",

    'resource_plan.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 5 sheets:
1. Resource Register & Calendar — merge the Resource Register with \
availability data; add an Availability % per week column alongside the \
register. Flag over-allocation (>100%) with red conditional formatting.
2. Resource Loading Table — week-by-week utilisation table, kept as is \
(most operationally important sheet).
3. Effort & Seniority Summary — merge Effort by Workstream/Phase and Seniority \
Mix into one summary sheet with two clearly labelled tables.
4. Resource Risk Log — kept as is.
5. Change Log.
Do not generate separate Resource Calendar, Capacity Plan, or Role \
Responsibility Profile sheets.

""",

    'raci_matrix.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. RACI Matrix — full matrix with frozen columns and rotated headers, kept \
as is. Apply one A per row validation.
2. Accountability & Sign-off Register — merge the Accountability Summary and \
Sign-off Register; accountability table at top, sign-off register below with \
a clear section header row.
3. RACI Validation Log — validation check results; fold role responsibility \
profiles into the Accountability sheet rather than a separate tab.
4. Change Log.
Do not generate separate Role Responsibility Profile or Governance RACI sheets \
(governance RACI lives in P1.6).

""",

    'budget_cost_baseline.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 5 sheets:
1. Budget Baseline & Tracker — merge the Budget Baseline and Cost Tracker; \
baseline columns sit alongside actuals/forecast so variance is visible in \
one view (Baseline Cost | Actual Cost | Forecast to Complete | Variance £ | \
Variance %).
2. Monthly Cost Profile — S-curve and monthly spend breakdown, kept as is.
3. Invoice Schedule — kept as is for T&M; replaced with Milestone Invoicing \
Schedule for Fixed Price (see fee structure adaptation below).
4. Financial Dashboard & EVM — merge the Financial Dashboard and Earned Value \
Analysis; KPI summary at top, EVM metrics (SPI, CPI, EAC, VAC, TCPI) below.
5. Change Log.
Do not generate separate Cost Baseline Snapshot or Budget Risk Log sheets \
(budget risks are captured in the Risk Register P2.7).

""",

    'risk_register.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 5 sheets:
1. Risk Register — full register with all columns; add a Status column \
(Open / Closed) and use filtering rather than a separate Closed Risk Archive \
sheet.
2. Heat Map — visual 3×3 heat map showing inherent and residual risk \
positions, kept as is.
3. Risk Response Plans — detailed mitigation actions per risk, kept as is.
4. Risk Trend & Dashboard — merge the Risk Trend Tracker (period-by-period \
heat map evolution) and Risk Reporting Dashboard (KPI summary); trend table \
at top, dashboard below.
5. Change Log.
Do not generate a separate Closed Risk Archive or standalone Risk Reporting \
Dashboard sheet.

""",

    'issue_dependency_log.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Issue Log & Escalation — merge the Issue Log and Escalation Tracker; add \
escalation columns directly to the issue log (Escalated Y/N | Escalation Date \
| Escalation Level | Escalation Outcome). Use a Status filter rather than a \
separate Closed Issues Archive.
2. Dependency Register — kept as is.
3. Issue-Risk Linkage Map — kept as is (the cross-reference is operationally \
important).
4. Change Log.
Do not generate separate Escalation Tracker, Resolution Dashboard, or Closed \
Issue Archive sheets.

""",

    'quality_plan.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Deliverable Review Schedule & Quality Gates — merge both; quality gate \
register as a second table below the review schedule with a clear section \
header.
2. Quality Checklist Library — kept as is (operationally critical for \
reviewers).
3. Non-Conformance Log & Metrics — merge the Non-Conformance Log, Quality \
Metrics Tracker, and Review Turnaround Tracker into one sheet with three \
clearly labelled sections separated by bold header rows.
4. Change Log.
Do not generate separate Quality Gate Register, Quality Metrics, or Review \
Turnaround Tracker sheets.

""",

    'change_control_plan.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 4 sheets:
1. Change Request Register & Impact — merge the Change Request Register and \
Impact Assessment Tracker; add impact columns directly to the register \
(Schedule Impact (days) | Budget Impact (£) | Resource Impact | Risk Impact | \
Scope Impact | Overall Impact Rating (Minor / Major / Emergency)). Use \
Status filtering for Closed changes rather than a separate archive.
2. Baseline Change Log — kept as is (full audit trail is essential).
3. Commercial Amendment Tracker & Dashboard — merge the Commercial Amendment \
Tracker and Change Control Dashboard; KPI summary at top, commercial tracker \
below with a clear section header. Embed the Change Freeze Calendar as a \
reference table in the lower section rather than a separate sheet.
4. Change Log.

""",

    'pmo_playbook.json': """\
WORKBOOK RATIONALISATION — generate a maximum of 5 sheets:
1. Engagement Dashboard — operational one-page summary with RAG statuses, \
kept as is.
2. Planning Document Index & Readiness Assessment — merge both; document index \
table at top, readiness assessment grid (ten dimensions) below.
3. RAID & Change Summary — merge RAID Summary and Change Request Summary; \
four clearly labelled sections: Risks | Issues | Dependencies & Assumptions | \
Changes.
4. Budget & Milestone Summary — merge Budget Summary and Milestone Tracker \
into one sheet with two clearly labelled tables.
5. Master Open Items & Change Log — open items at top, change log below, \
separated by a bold section divider row.
Do not generate a separate Process Quick Reference sheet — these summaries are \
embedded in the Word and PowerPoint playbook documents.

""",

    'status_reporting_template.json': """\
WORKBOOK RATIONALISATION — the Excel dashboard should have a maximum of 4 \
sheets:
1. Programme Dashboard — single-page summary with RAG statuses and KPIs, \
kept as is.
2. Status Data Input — merge Milestone Data, Risk Data, Issue Data, and \
Workstream Status into one structured input sheet with clearly labelled \
sections separated by bold header rows.
3. Financial Data Input — merge Financial Data and Period History into one \
sheet.
4. Change Log.
Do not generate additional separate data sheets.

""",
}

# ── 4. Fee Structure Branch (budget_cost_baseline.json) ─────────────────────

FEE_Q0 = """\
0. **Fee Structure Confirmation (resolve before all other questions)**
The Engagement Context above indicates the fee structure is \
[Fee Structure from context block]. Confirm which financial model applies \
before proceeding, as it changes the entire structure of this deliverable:

- **Time and Materials (T&M)**: Cost baseline = effort × daily rate per role. \
Budget tracks actual cost vs approved budget. Over-spend is billable if within \
scope.
- **Fixed Price**: A fixed fee is agreed regardless of actual effort. The \
baseline tracks cost-to-complete against the fixed envelope — margin erosion \
is the key risk. Invoicing follows agreed milestones, not time consumed.
- **Capped T&M**: Time and materials up to an agreed maximum cap. The baseline \
tracks both rate × effort and proximity to the cap.

Please confirm: which fee structure applies? If Fixed Price or Capped T&M, \
provide the agreed fee amount and the invoicing milestone schedule.

"""

FEE_BUILD = """\
FEE STRUCTURE ADAPTATION

Apply the following model before generating any Excel sheets:

**If Time and Materials:**
- Cost baseline: Effort Hours × Daily Rate per Role per Workstream per Month.
- Track: Planned Cost | Actual Cost | Forecast to Complete | Variance.
- Include EVM metrics: SPI, CPI, EAC, VAC, TCPI.

**If Fixed Price:**
- Replace the T&M cost build with a Fixed Price Cost Control model:
  - Fixed Fee: [confirmed amount]
  - Estimated Internal Cost to Deliver: effort × internal rates from Resource Plan
  - Gross Margin: Fixed Fee minus Internal Cost
  - Cost to Complete (CTC): remaining estimated cost
  - Earned Value: % of deliverables signed off × Fixed Fee
  - Margin at Risk: CTC vs remaining Fixed Fee
- Replace the Invoice Schedule sheet with a Milestone Invoicing Schedule: \
Milestone | Invoiceable Amount | Invoice Date | Status.
- Add a Margin Tracker table to the Financial Dashboard & EVM sheet: \
Month | Planned Cost | Actual Cost | Fixed Fee Earned | Margin £ | Margin %.

**If Capped T&M:**
- Build as T&M above and add:
  - Cap Amount column (the agreed NTE cap per period or total).
  - Cap Utilisation % = (Actual + Forecast to Complete) ÷ Cap Amount.
  - Colour warning: orange when Cap Utilisation > 80%, red when > 95%.

---

"""

# ── 5. Methodology Branch ────────────────────────────────────────────────────

METHOD_Q0_SCHEDULE = """\
0. **Delivery Methodology Confirmation (resolve before all other questions)**
The Engagement Context above indicates the delivery methodology is \
[Delivery Methodology from context block]. The schedule approach differs \
significantly by methodology:

- **Waterfall**: Phase-gate schedule with sequential milestones, baselines, \
and critical path. Full Gantt chart. Schedule is the primary tracking tool.
- **Agile**: Sprint-based delivery with a release roadmap and velocity \
tracking. A high-level milestone plan exists for major releases and phase \
boundaries but detailed task scheduling is managed within sprints. A full \
Gantt and critical path analysis are not appropriate.
- **Hybrid**: Phase-gate milestones for governance and reporting; sprint-based \
execution within phases. Both Milestone Tracker and Sprint Plan sheets apply.

Please confirm the delivery methodology. If Agile or Hybrid, also confirm: \
sprint length (weeks), number of sprints planned, sprint ceremony cadence \
(planning / review / retrospective), and how milestone dates will be \
communicated to Waterfall-reporting stakeholders.

"""

METHOD_BUILD_SCHEDULE = """\
METHODOLOGY ADAPTATION — SCHEDULE

Apply the following before generating any deliverable content:

**If Waterfall:**
- Build the full Project Schedule & Gantt sheet with week-by-week Gantt bars \
using conditional formatting.
- Milestone Tracker columns: Baseline Date | Planned Date | Forecast Date | \
Actual Date | Variance (days).
- Delete the Sprint Plan sheet.
- Include a Critical Path summary paragraph in the Word document noting that \
the full CPM analysis is in P2.3.

**If Agile:**
- Replace the Project Schedule & Gantt sheet with a Release Roadmap table: \
Sprint Number | Sprint Goal | Start Date | End Date | Planned Velocity \
(story points) | Key Deliverables.
- Keep the Sprint Plan sheet as the primary scheduling tool. Add a Velocity \
Tracker table: Sprint | Planned Points | Completed Points | Velocity | Running \
Average Velocity.
- The Milestone Tracker contains only major phase boundaries and governance \
milestones — not sprint-level tasks.
- Remove CPM predecessor/successor columns (not applicable to Agile).
- Note in the Word document: "Sprint-level scheduling is managed in the Sprint \
Plan tab. Milestone dates represent phase commitments to client governance."

**If Hybrid:**
- Build both: Milestone Tracker for phase-level governance milestones \
(Waterfall-style reporting) and Sprint Plan sheet for execution tracking \
(Agile delivery).
- The Gantt chart shows phase-level bars only, not task-level detail.
- Note in the Word document: "Sprint-level scheduling is managed in the Sprint \
Plan tab. Milestone dates above represent phase commitments to client \
governance."

---

"""

METHOD_Q0_CPM = """\
0. **Delivery Methodology Confirmation (resolve before all other questions)**
The Engagement Context above indicates the delivery methodology is \
[Delivery Methodology from context block].

Critical Path Method (CPM) is a Waterfall planning technique and is NOT \
applicable to pure Agile delivery, where work is sequenced in sprints rather \
than by task predecessor relationships.

- **Waterfall or Hybrid**: Proceed with the full CPM analysis as described \
in this prompt.
- **Agile**: Do not generate a Critical Path analysis. Instead generate a \
Sprint Dependency Map — see the Agile variant in the Build step below.

Please confirm: Waterfall, Agile, or Hybrid?

"""

METHOD_BUILD_CPM = """\
METHODOLOGY ADAPTATION — CRITICAL PATH

Apply the following at the start of the build step:

**If Agile:**
Do not generate the Critical Path Analysis described below. Instead generate:
- Word document titled "Sprint Dependency Map": a narrative and table showing \
which sprint deliverables are inputs to subsequent sprints, identifying \
cross-sprint blockers and the minimum viable sprint sequence.
- Excel workbook (4 sheets): Sprint Dependency Register (Sprint | Deliverable \
| Dependent Sprint | Dependency Type | Risk if Late | Mitigation) | Blocker \
Log | Sprint Sequence Map (visual table) | Change Log.

**If Waterfall or Hybrid:**
Proceed with the full Critical Path Analysis as specified below.

---

"""

# ── 6. Cross-Document Consistency Audit (pmo_playbook.json) ─────────────────

CONSISTENCY_AUDIT = """\
CROSS-DOCUMENT CONSISTENCY AUDIT

Before building the PMO Playbook, run the following checks across all provided \
planning documents. Flag each as PASS / FAIL / WARNING with a brief finding.

**Scope Consistency**
- Do the WBS Level 2 workstreams (P2.1) match the workstreams in the Scope \
Statement (P1.3) and Engagement Charter (P1.5)?
- Are all scope inclusions from P1.3 represented by at least one WBS element?
- Are all scope exclusions from P1.3 absent from the WBS?

**Date Consistency**
- Does the engagement start date in the Schedule (P2.2) match the Charter \
start date (P1.5)?
- Does the engagement end date in the Schedule (P2.2) match the Charter end \
date (P1.5)?
- Do Resource Plan start/end dates (P2.4) fall within Schedule dates (P2.2)?
- Are major milestone dates consistent between Schedule (P2.2) and Critical \
Path (P2.3)?

**Resource and Budget Consistency**
- Do all roles in the RACI Matrix (P2.5) correspond to roles in the Resource \
Plan (P2.4)?
- Does total effort in the Resource Plan (P2.4) align with the effort used to \
build the Budget (P2.6) within a 5% tolerance?
- Do Budget monthly cost peaks (P2.6) align with Resource loading peaks \
(P2.4) by month?

**Governance Consistency**
- Are all governance bodies from the Governance Framework (P1.6) referenced \
in the Communications Plan (P2.9)?
- Do escalation paths in the Risk Register (P2.7) and Issue Log (P2.8) \
reference governance bodies that exist in P1.6?
- Does the Change Control Plan (P2.12) authority matrix reference decision \
makers who appear in the RACI (P2.5) and Governance Framework (P1.6)?

**Open Items Consolidation**
- Consolidate all open items from all 17 planning documents into the Master \
Open Items sheet.
- Flag any item marked "Blocks Delivery Start".
- Flag any item raised in a P1.x step but never resolved in a later step.

Report all FAIL and WARNING findings in a table in the Word document:
Document(s) | Inconsistency Found | Recommended Resolution | \
Blocks Delivery Start (Y/N)

If there are more than 5 FAIL findings, prepend the following banner to the \
playbook cover slide:
"⚠️ Significant planning inconsistencies detected. Resolve all FAIL items \
before distributing this playbook. Known conflicts are in the Consistency \
Audit section."

---

"""


# ── Helper: find the Excel section anchor ────────────────────────────────────

def find_excel_anchor(inst):
    for anchor in ('EXCEL WORKBOOK STRUCTURE', 'PWC FORMATTING STANDARDS FOR EXCEL'):
        idx = inst.find(anchor)
        if idx >= 0:
            return idx, anchor
    return -1, None


# ── Helper: find and insert Q0 before first numbered question in Step 1 ──────

def insert_q0_in_step1(inst, step1_anchor, q0_text):
    """Insert q0_text before the first '1. ' after step1_anchor."""
    step1_idx = inst.find(step1_anchor)
    if step1_idx < 0:
        return inst
    search_from = step1_idx
    # Find first occurrence of '\n1. ' after the STEP 1 heading
    q1_idx = inst.find('\n1. ', search_from)
    if q1_idx < 0:
        return inst
    return inst[:q1_idx + 1] + q0_text + inst[q1_idx + 1:]


# ── Helper: insert text right after STEP 3 line ──────────────────────────────

def insert_after_step3(inst, insert_text):
    step3_idx = inst.find('STEP 3 — BUILD')
    if step3_idx < 0:
        step3_idx = inst.find('STEP 3 —')
    if step3_idx < 0:
        return inst
    # Move to end of that line
    eol = inst.find('\n', step3_idx)
    if eol < 0:
        return inst
    return inst[:eol + 1] + '\n' + insert_text + inst[eol + 1:]


# ── Main processing loop ──────────────────────────────────────────────────────

def process_file(fname):
    path = PROMPTS_DIR / fname
    with path.open('r', encoding='utf-8') as fh:
        data = json.load(fh)

    inst = data['instruction']
    artifact = data.get('artifact', fname.replace('.json', '').replace('_', ' ').title())
    changed = False

    # 1. Context block
    if 'ENGAGEMENT CONTEXT' not in inst:
        inst = CONTEXT_BLOCK + inst
        changed = True

    # 2. Thin-context warning
    if 'CONTEXT CHECK' not in inst:
        step1_idx = inst.find('STEP 1 —')
        if step1_idx < 0:
            step1_idx = inst.find('STEP 1:')
        if step1_idx >= 0:
            inst = inst[:step1_idx] + thin_context_warning(artifact) + inst[step1_idx:]
            changed = True

    # 3. Excel rationalisation directive
    if fname in EXCEL_RATIONALISATIONS and 'WORKBOOK RATIONALISATION' not in inst and 'NOTE: The Engagement Charter' not in inst:
        excel_idx, anchor = find_excel_anchor(inst)
        if excel_idx >= 0:
            inst = inst[:excel_idx] + EXCEL_RATIONALISATIONS[fname] + inst[excel_idx:]
            changed = True
        elif fname == 'engagement_charter.json':
            # No Excel section — just add the note before Step 3
            step3_idx = inst.find('STEP 3')
            if step3_idx >= 0:
                inst = inst[:step3_idx] + EXCEL_RATIONALISATIONS[fname] + inst[step3_idx:]
                changed = True

    # 4. Fee structure branch (budget only)
    if fname == 'budget_cost_baseline.json':
        if 'Fee Structure Confirmation' not in inst:
            inst = insert_q0_in_step1(inst, 'STEP 1 —', FEE_Q0)
            changed = True
        if 'FEE STRUCTURE ADAPTATION' not in inst:
            inst = insert_after_step3(inst, FEE_BUILD)
            changed = True

    # 5a. Methodology branch — schedule
    if fname == 'schedule_milestones.json':
        if 'Delivery Methodology Confirmation' not in inst:
            inst = insert_q0_in_step1(inst, 'STEP 1 —', METHOD_Q0_SCHEDULE)
            changed = True
        if 'METHODOLOGY ADAPTATION — SCHEDULE' not in inst:
            inst = insert_after_step3(inst, METHOD_BUILD_SCHEDULE)
            changed = True

    # 5b. Methodology branch — critical path
    if fname == 'critical_path.json':
        if 'Delivery Methodology Confirmation' not in inst:
            inst = insert_q0_in_step1(inst, 'STEP 1 —', METHOD_Q0_CPM)
            changed = True
        if 'METHODOLOGY ADAPTATION — CRITICAL PATH' not in inst:
            inst = insert_after_step3(inst, METHOD_BUILD_CPM)
            changed = True

    # 6. Consistency audit (pmo playbook only)
    if fname == 'pmo_playbook.json' and 'CROSS-DOCUMENT CONSISTENCY AUDIT' not in inst:
        step1_idx = inst.find('STEP 1 — CONSOLIDATION REVIEW')
        if step1_idx >= 0:
            eol = inst.find('\n', step1_idx)
            inst = inst[:eol + 1] + '\n' + CONSISTENCY_AUDIT + inst[eol + 1:]
            changed = True

    if changed:
        data['instruction'] = inst
        with path.open('w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f'  UPDATED: {fname}')
    else:
        print(f'  SKIPPED (no changes needed): {fname}')

    return changed


def main():
    if not PROMPTS_DIR.exists():
        print(f'ERROR: prompts directory not found: {PROMPTS_DIR}')
        sys.exit(1)

    files = sorted(path.name for path in PROMPTS_DIR.glob('*.json'))
    updated = 0
    skipped = 0
    for fname in files:
        if fname in SKIP_FILES:
            print(f'  SKIP (excluded): {fname}')
            skipped += 1
            continue
        process_file(fname)
        updated += 1

    print(f'\nDone. {updated} files processed, {skipped} excluded.')


if __name__ == '__main__':
    main()
