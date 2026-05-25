# Investment Readiness Screener

**Operational insight, built on data.**
Crystal Olisa · Operations Generalist · [LinkedIn](https://linkedin.com/in/crystalolisa) · [Portfolio](https://github.com/crystalolisa)


## The business problem

When companies submit financials for investment consideration, someone has to read them. At Asoko Insight, that review was manual — four signals extracted per company, a decision made, a pipeline managed. The process worked. It was also slow, inconsistent across reviewers, and produced no audit trail.

This project automates the first-pass screen. The same four signals, the same decision logic, applied systematically. What took 48 hours of manual review runs in seconds — with every decision traceable to a documented threshold. That shift moves analyst capacity from data extraction to the conversations that actually require judgment.


## Dataset

**Source:** Synthetic — 50 African companies across 7 sectors and 10 countries.

Generated to reflect the realistic variance in submitted financials: strong companies that clear all four thresholds, borderline companies that fail on one or two signals, and weak companies that fail across the board. Sectors include Fintech, Agribusiness, Retail, Manufacturing, Energy, Logistics, and Healthcare. Countries span Nigeria, Kenya, Ghana, South Africa, Ethiopia, Rwanda, Tanzania, Uganda, Senegal, and Egypt.


## Screening thresholds

| Signal | Threshold | Rationale |
|---|---|---|
| Revenue | ≥ $1M USD | Minimum viable scale for institutional investment conversation |
| EBITDA margin | ≥ 15% | Operational efficiency floor |
| Revenue growth (YoY) | ≥ 10% | Demonstrates trajectory, not just current position |
| Debt-to-equity ratio | ≤ 2.0 | Leverage ceiling before structural risk flags |

**Decision logic:** All four signals passed → **Advance**. Two or three signals passed → **Review**. Fewer than two → **Decline**.


## Findings

### 1. Pipeline conversion — what proportion is investable

![Screening outcome distribution](investment_readiness_screener/charts/chart_1_screening_outcomes.png)

Across 50 companies, the screen produced: 7 Advance (14%), 40 Review (80%), 3 Decline (6%). The large Review pool is the operational finding — 80% of the pipeline requires analyst judgment, not a binary pass or fail. The screen doesn't eliminate that work. It organises it, so analysts know exactly which signal caused the Review flag before opening a single spreadsheet. The Advance rate at 14% reflects the threshold stringency — too high and the thresholds need tightening; too low and the sourcing criteria needs recalibrating.


### 2. Signal failure pattern — where the pipeline is breaking down

![Signal failure breakdown](investment_readiness_screener/charts/chart_2_signal_failures.png)

EBITDA margin is the most common failure signal — 23 of 50 companies (46%) fell below the 15% efficiency floor. Revenue growth failed in 38% of cases. These two signals together tell a specific sourcing story: the pipeline is finding companies with revenue and manageable leverage, but operational efficiency is the consistent gap. That's not a data quality problem — it's a sourcing criteria problem. A pipeline that consistently fails on margin is pulling in companies too early in their efficiency curve.


### 3. EBITDA margin vs revenue — population shape

![EBITDA vs revenue scatter](investment_readiness_screener/charts/chart_3_ebitda_vs_growth.png)

The scatter shows where the investable companies cluster and whether the Review category is genuinely borderline or just failing on one specific signal. A pipeline concentrated in the lower-left quadrant (low revenue, low margin) is a sourcing problem. A pipeline with strong revenue but weak margin is an efficiency problem. The visual separates those two diagnoses in a way the summary table cannot.


## Analytical decisions

**Three-tier flag rather than binary pass/fail.** A company that clears three of four signals is not the same as a company that clears one. Collapsing both into Decline loses information that changes the analyst's next action. The Review flag preserves that nuance.

**Thresholds as named constants.** Every threshold is defined once at the top of the notebook as a named variable. Changing a threshold means changing one number, not hunting through formulas. The decision logic is separated from the criteria.

**Signal failure chart sorted by failure rate.** The sort order is not arbitrary — the chart is designed to answer "where is the pipeline breaking down most?" not "how are signals ordered alphabetically."


## Methodology

**Investment flag logic:** Advance = 4 signals passed. Review = 2–3 signals passed. Decline = 0–1 signals passed.

**EBITDA margin** is used as the primary efficiency signal rather than absolute EBITDA, because absolute EBITDA is a function of revenue size — a $20M revenue company with 5% margin is not comparable to a $1M revenue company with 5% margin. Margin normalises for scale.

**Debt-to-equity ratio** is the leverage signal. A ratio above 2.0 indicates the company is carrying more than twice as much debt as equity — a structural risk flag before deeper due diligence begins.

**Synthetic data note:** The dataset was generated to produce realistic variance across the three outcome categories. In a real workflow, the input data would be extracted from submitted PDFs or structured Excel submissions. The screening logic here is dataset-agnostic — it runs on any input that produces the same four columns.


## Metric glossary

**EBITDA margin** — Earnings Before Interest, Tax, Depreciation and Amortisation as a percentage of revenue. Measures operational efficiency independent of capital structure and accounting choices.

**Revenue growth (YoY)** — Year-on-year revenue growth rate. Measures trajectory rather than current position — a flat company with high revenue is a different investment case to a growing company with moderate revenue.

**Debt-to-equity ratio** — Total debt divided by total equity. Measures leverage. A ratio above 2.0 means the company is more than twice as leveraged as it is equity-funded.

**Advance / Review / Decline** — The three-tier output of the screening system. Advance = cleared all four thresholds. Review = cleared two or three. Decline = cleared fewer than two.


## Repo structure

```
investment_readiness_screener/
├── README.md
├── notebooks/
│   └── investment_screener.ipynb
├── data/
│   ├── african_companies_financials.csv
│   └── screening_results.csv
└── charts/
    ├── chart_1_screening_outcomes.png
    ├── chart_2_signal_failures.png
    └── chart_3_ebitda_vs_growth.png
```


## Key outputs

- Screening outcome distribution — pipeline conversion at each stage (Chart 1)
- Signal failure breakdown — where the pipeline is breaking down and why (Chart 2)
- EBITDA margin vs revenue scatter — investability population map (Chart 3)
- Full screening results table with per-signal flags (exported to `screening_results.csv`)
- Sector and country breakdown of screening outcomes


## Notebook

[Project A Notebook →](notebooks/investment_screener.ipynb)


*The screen does not replace the investment conversation. It makes the right conversations possible faster.*
