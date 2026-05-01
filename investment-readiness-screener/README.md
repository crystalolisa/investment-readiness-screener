# Investment Readiness Screener — Project A

**Operational insight, built on data.**
Crystal Olisa · Operations Generalist · [LinkedIn](https://linkedin.com/in/crystalolisa) · [Portfolio](https://github.com/crystalolisa)

---

## The business problem

When a company submits financials for investment consideration, the first question isn't whether they're investable — it's whether the submission is complete enough to assess. In a pipeline of African SMEs across multiple currencies, sectors, and documentation standards, that triage step alone determines whether the screen produces reliable decisions or noise.

As a Digital Engagement Analyst supporting private equity DealRooms for African SMEs, I coordinated the intake, validation, and review of submitted company financials across active investment pipelines. Four signals drove the first-pass assessment — revenue size, EBITDA margin, revenue growth, and debt load — and every company needed a documented decision: advance, decline, or defer.

The screening decision itself was fast. The bottleneck was everything before it — pulling revenue, EBITDA components, debt and equity figures from 15–20 page audited PDFs, converting currencies, cross-checking figures, and formatting into a structure the screen could actually use. At 100 submissions per cycle, that extraction and standardisation step alone consumed 75–125 analyst hours before a single investment decision was made.

This project automates that layer. Not just the screen — the full pipeline, from structured intake form to validated investment flag, with every decision documented and every threshold adjustable. The same 75–125 hours of extraction work runs in under 10 seconds.

---

## Project architecture

This is a three-phase pipeline. Each phase has a distinct responsibility.

| Phase | File | Input | Output |
|---|---|---|---|
| 1 — Ingestion | `generate_profiles.py` | World Bank calibration data | 100 JSON company profiles |
| 2 — Extraction | `pipeline/extract_and_validate.py` | 100 JSON profiles | `screening_results.csv` |
| 3 — Screening | `notebooks/investment_screener_v1.ipynb` | `screening_results.csv` | Investment flags + charts |

The three phases are deliberately separated. Phase 1 is data generation. Phase 2 is validation and standardisation. Phase 3 is analysis. Combining them into a single script would produce a cleaner file count but would collapse the distinction between a data quality problem and a screening decision — which are operationally different things that require different follow-up actions.

---

## Source data and calibration

**World Bank Enterprise Surveys — public indicator data**
Source: Enterprise Surveys, World Bank Group. https://www.enterprisesurveys.org
Classification: Public. No registration required for indicator-level data.

Four indicator files downloaded for Nigeria, Kenya, Ghana, South Africa, and Ethiopia:

| File | Indicator | Use in project |
|---|---|---|
| `WB_ES_T_PERF1.csv` | Real annual sales growth (%) — all sectors | Calibrates revenue growth ranges per archetype |
| `WB_ES_M_PERF1.csv` | Real annual sales growth (%) — manufacturing | Sector-level growth reference |
| `WB_ES_S_PERF1.csv` | Real annual sales growth (%) — services | Sector-level growth reference |
| `WB_ES_T_FIN16.csv` | % of firms identifying access to finance as a major constraint | Calibrates submission quality / completeness split |

**Calibration outputs used in data generation:**

| Parameter | Value | Source |
|---|---|---|
| Growth median (5 countries) | 0.2% | WB_ES_T_PERF1 |
| Growth P25 | -10.2% | WB_ES_T_PERF1 |
| Growth P75 | 5.6% | WB_ES_T_PERF1 |
| Finance constraint median | 33.1% | WB_ES_T_FIN16 |

The finance constraint median (33.1%) is used as a proxy for submission quality — a pipeline where one in three companies identifies access to finance as a major constraint will naturally produce inconsistent or incomplete documentation. The completeness split between Validated and Partial submissions is calibrated to this figure. Submissions that cannot pass the intake form's completeness requirements do not reach the pipeline.

**Submission quality split (screenable submissions only):**

| Status | Completeness score | Description |
|---|---|---|
| Validated | 85–100 | All fields present and reconciled |
| Partial | 55–80 | One or two non-critical fields missing — mirrors WB 33% finance constraint rate |

---

## Synthetic data design

The dataset is synthetic — 100 companies generated to reflect realistic African mid-market SME pipeline variance. Synthetic data was the right choice here: the pipeline's value is in the architecture, not the dataset. The distributions are anchored to published World Bank indicators so the variance is realistic, but the companies are fabricated to avoid any dependency on confidential data. The World Bank microdata requires a signed confidentiality agreement; the indicator-level data used here does not.

**What synthetic means here:** The company names, registration numbers, and specific financial figures are fabricated. The distributions, growth ranges, completeness rates, and archetype proportions are calibrated to published World Bank indicators for Sub-Saharan Africa.

**Six company archetypes and their WB calibration:**

| Archetype | Count | Revenue | EBITDA margin | Growth (WB calibration) | D/E |
|---|---|---|---|---|---|
| Qualified Star | 18 | $1.5M–$30M | 15%–35% | 10%–20% (above WB P75) | 0.3–1.8 |
| Scale-up | 15 | $0.5M–$10M | -15%–8% (burning cash) | 20%–80% (high growth, negative margin) | 0.8–2.8 |
| Mature Pillar | 14 | $2M–$25M | 18%–30% | -10.2% to 5.6% (WB P25–P75) | 2.2–4.5 |
| Semi-qualified | 20 | $0.8M–$8M | 5%–18% | WB P25 to 12% | 1.0–3.2 |
| Unqualified | 16 | $0.05M–$0.95M | -25%–5% | -25% to WB median | 2.8–6.5 |
| Deferred | 17 | $0.1M–$2M | n/a | n/a (no prior year) | 0.5–3.0 |

Note: 9 additional companies were deferred at Gate 3 — generated as non-Deferred archetypes (including 2 Qualified Stars) but submitted only one year of accounts. Their financial profiles were strong; the deferral reflects the submission, not the business.

**Currency realism:** Revenue is generated in local currency (NGN, KES, GHS, ZAR, ETB, RWF, TZS, UGX, XOF, EGP) and converted to USD using historical exchange rates embedded in each JSON profile. The conversion chain is preserved in the master CSV so every USD figure is auditable back to its local currency source.

---

## Submission form schema

Companies submit a structured JSON form — not a PDF. The standardised form was chosen deliberately: it positions intake as a design decision. The structure of what you collect shapes the quality of what you can assess. A form that captures gross profit and operating expenses separately, for example, makes EBITDA reconciliation possible. A form that only asks for a submitted EBITDA figure does not.

Each submission captures:

```
submission_id, submission_date, submission_status
company: name, country, currency, fx_rate, sector, registration_number, year_founded
financials: reporting_year, audit_status, revenue, cost_of_sales, gross_profit,
            operating_expenses, ebitda, finance_costs, profit_before_tax,
            total_debt, total_equity
prior_year_financials: reporting_year, revenue, audit_status
designated_contact: role
documents: income_statement_ref, balance_sheet_ref, prior_year_accounts_ref, registration_doc_ref
data_quality: completeness_score, missing_fields, reviewer_notes  ← legacy fields (see note below)
```

**Note on `data_quality.missing_fields`:** In a live system, this field would not exist — the intake form enforces completeness before submission, so no submission with missing critical fields reaches the pipeline. In this synthetic dataset the field is retained as a legacy artefact from earlier pipeline versions. The field carries no operational weight; Gate 1 and Gate 3 enforce the actual completeness rules.

**Key schema decisions:**

Prior year revenue is captured as a submitted field, not a growth rate. The pipeline calculates YoY growth itself from the two revenue figures. This separates the raw data from the derived metric and makes the calculation auditable.

EBITDA is submitted but also cross-checked against components (gross profit minus operating expenses) in Gate 4. The two values should agree within 5%. A larger variance flags the submission for reviewer check before the figure is used in a screening decision.

---

## Pipeline gate logic

Five gates run in sequence before any screening logic is applied.

**Gate 1 — Operational maturity**
Condition: `reporting_year − year_founded < 3`
Action: Deferred — exit pipeline immediately.
Rationale: EBITDA from fewer than three years of operations is not a reliable signal. The company has not demonstrated sufficient operating history for investment consideration. This is not negotiable — three years is the minimum, not a guideline.

**Gate 2 — Submission integrity (non-blocking)**
Condition: Duplicate document references across submission fields + unaudited or management accounts status.
Action: ⚑ Submission Anomaly flag — internal only. Pipeline continues.
Rationale: A founder who uploads the same document in multiple required fields to satisfy intake is signalling they do not have the required documentation. Combined with an unaudited status, this warrants reviewer scrutiny before any pipeline time is spent. This flag does not change the investment outcome — it changes the internal handling. A company can be flagged Anomaly and still Advance, Decline, or be Deferred.

**Gate 3 — Financial history**
Condition: Prior year revenue absent from submission.
Action: Deferred — exit pipeline immediately.
Rationale: Year-on-year growth cannot be calculated from a single year of accounts. A company cannot be evaluated as meeting or not meeting investment criteria without a full assessment across all four criteria. Each criterion is individually necessary — the others do not compensate for its absence. This is not a soft flag. A strong debt-to-equity ratio in year one does not indicate capital structure in year two. Partial data produces false confidence.

**Gate 4 — EBITDA reconciliation (non-blocking)**
Condition: |submitted_ebitda − (gross_profit − operating_expenses)| / derived > 5%
Action: Flag the submission. Continue to screening.
Rationale: Submitted EBITDA is cross-checked against the derived figure. The variance may reflect a legitimate accounting treatment (depreciation, one-off items). Flagged for reviewer verification before advancing.

**Gate 5 — Standardisation and metric derivation**
Action: Convert local currency to USD millions. Calculate EBITDA margin, YoY growth, debt-to-equity. Compile master CSV.

**Operational implementation note**

In a live environment, each gate would trigger a distinct downstream action. Gate 1 and Gate 3 deferrals would generate an automated notification to the founder with their resubmission eligibility date and the specific reason for deferral. Gate 2 anomaly flags would create an internal reviewer task with the duplicate document details attached — no founder notification. Gate 4 EBITDA reconciliation flags would create a reviewer task with the variance figure. Gate 5 completions would update the company's pipeline stage automatically. The gate logic here is the decision layer. The operational layer — CRM workflow routing, automated notifications, reviewer task creation — sits on top of it.

---

## Screening criteria

| Criterion | Threshold |
|---|---|
| Revenue (USD) | > $1.5M |
| EBITDA margin | ≥ 15% |
| Revenue growth (YoY) | ≥ 10% |
| Debt-to-equity ratio | ≤ 2.0 |

**Decision logic:** All four criteria must be assessable and must clear the threshold. No exceptions.

A company cannot be evaluated as investable on three out of four criteria. Each criterion is individually necessary. A strong result on three does not compensate for an unknown or failing fourth — a strong debt-to-equity ratio in the first year of assessed accounts says nothing about capital structure after the next growth phase. Partial assessments produce false confidence. The end client is a private equity fund. There is no investment conversation without a complete picture.

**Three founder-facing outcomes:**
- **Advance** — all four criteria met
- **Decline** — one or more criteria not met
- **Deferred** — Gate 0 (operating history) or Gate 0.6 (financial history) failure

**One internal flag (never shown to founders):**
- **⚑ Submission Anomaly** — duplicate document references + unaudited or management accounts status

---

## Pipeline results

![Pipeline conversion funnel](project_a/charts/chart_1_pipeline_funnel.png)

**Pipeline attrition by gate:**

| Gate | Action | Companies exited |
|---|---|---|
| Gate 1 — Operational maturity | Deferred | 17 |
| Gate 2 — Submission integrity | Flagged (non-blocking) | 0 exited |
| Gate 3 — Financial history | Deferred | 9 |
| Gate 4 — EBITDA reconciliation | Flagged (non-blocking) | 0 exited |
| Gate 5 — Screening | Advance or Decline | 74 assessed |

**Final outcome distribution:**

| Outcome | Count | % of total |
|---|---|---|
| **Advance** | **11** | **11%** |
| Decline | 63 | 63% |
| Deferred — operating history (Gate 1) | 17 | 17% |
| Deferred — financial history (Gate 3) | 9 | 9% |

**Submission anomaly outcomes (internal):**
9 companies were flagged ⚑ Submission Anomaly at Gate 2. None Advance — 8 Decline, 1 Deferred. The flag did not change their outcome; it changes how the reviewer handles their file. The correlation between anomaly flags and non-Advance outcomes is consistent with the flag's design: companies submitting duplicate documents under an unaudited status are unlikely to have the financial profile required to Advance.

5 companies had EBITDA reconciliation notes at Gate 4 and proceeded to screening with the variance noted.

---

## Analytical decisions

| Decision | Rationale |
|---|---|
| Minimum 3 years operating history (Gate 1) | Not a guideline — a minimum. Three years is the point at which operating patterns are established enough to be meaningful signals. |
| Minimum 2 years of audited accounts (Gate 3) | YoY growth requires two consecutive years. A company cannot be assessed on three out of four criteria. Each is individually necessary. |
| ⚑ Submission Anomaly non-blocking (Gate 2) | The flag changes internal handling, not the outcome. A reviewer decides the next step — the pipeline doesn't make that call automatically. |
| EBITDA reconciliation non-blocking (Gate 4) | Variance may be a legitimate accounting treatment. Flagged for human verification, not auto-rejected. |
| 4/4 criteria required for Advance | Partial data produces false confidence. The end client is a PE fund — there is no investment conversation without a complete picture. |
| No Review category | A complete submission either meets the criteria or it doesn't. Review was a middle ground with no corresponding investment decision. |
| Deferred over Declined for history failures | A company with insufficient operating or financial history isn't wrong — it's early. Deferred preserves the relationship and gives a concrete resubmission path. |
| Submission Anomaly internal only | You don't tell a founder they're flagged for submission irregularities. A human reviews the evidence and decides the next action. |

---

## Repo structure

```
project_a/
├── README_v7.md
├── generate_profiles.py
├── pipeline/
│   └── extract_and_validate.py
├── notebooks/
│   └── investment_screener_v1.ipynb
├── company_profiles/
│   └── AF001.json … AF100.json
├── data/
│   ├── WB_ES_T_PERF1.csv
│   ├── WB_ES_M_PERF1.csv
│   ├── WB_ES_S_PERF1.csv
│   ├── WB_ES_T_FIN16.csv
│   └── screening_results.csv
├── part2/
│   ├── dashboard.html
│   └── founder_reports/
│       └── AF001.html … AF100.html
└── charts/
    ├── chart_1_pipeline_funnel.png
    ├── chart_2_signal_failures.png
    ├── chart_3_ebitda_vs_revenue.png
    └── chart_4_pipeline_health.png
```

---

## Key outputs

**Part 1 — Screening pipeline**
- Pipeline conversion funnel — 100 submissions through four gates (Chart 1)
- Criteria failure breakdown — where the pipeline loses companies and why (Chart 2)
- EBITDA margin vs revenue scatter — investability population map (Chart 3)
- Pipeline health dashboard — status breakdown and completeness distribution (Chart 4)
- `screening_results.csv` — per-company derived metrics and gate outcomes

**Part 2 — Response and visibility layer**
- `part2/dashboard.html` — internal team view, all 100 companies, filterable, full detail on click
- `part2/founder_reports/` — 100 individual founder reports, one per submission, tailored by outcome

---

## Notebook

[Phase 3 Screening Notebook →](notebooks/investment_screener_v1.ipynb)

---

*The pipeline does not replace the investment conversation. It makes the right conversations possible faster.*
