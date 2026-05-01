"""
Investment Readiness Screener — Phase 1: Profile Generation
============================================================
Crystal Olisa · Operations Generalist

Generates 100 structured JSON company submission forms simulating
a realistic African SME investment pipeline.

Synthetic data distributions are calibrated against World Bank
Enterprise Survey public indicator data for Nigeria, Kenya, Ghana,
South Africa, and Ethiopia.

Source: Enterprise Surveys, World Bank Group.
https://www.enterprisesurveys.org
Classification: Public. No registration required for indicator-level data.

Calibration inputs (from data/ folder):
  WB_ES_T_PERF1.csv — Real annual sales growth (%)
  WB_ES_T_FIN16.csv — % of firms citing finance as major constraint

Output: company_profiles/AF001.json … AF100.json

Each profile includes: company details, financials, prior year financials (where applicable),
document references, data quality indicators, a designated_contact field (role: CEO),
and internal _meta fields for pipeline use.

Usage:
  python generate_profiles.py
"""

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = Path(__file__).parent / 'data'
PROFILES_DIR = Path(__file__).parent / 'company_profiles'
PROFILES_DIR.mkdir(exist_ok=True)

# ── Load World Bank calibration data ──────────────────────────────────────────
TARGET_COUNTRIES = ['NGA', 'KEN', 'GHA', 'ZAF', 'ETH']

df_growth = pd.read_csv(DATA_DIR / 'WB_ES_T_PERF1.csv')
growth_vals = df_growth[
    (df_growth['REF_AREA'].isin(TARGET_COUNTRIES)) &
    (df_growth['COMP_BREAKDOWN_1'] == '_T') &
    (df_growth['COMP_BREAKDOWN_2'] == '_T') &
    (df_growth['COMP_BREAKDOWN_3'] == '_T')
]['OBS_VALUE']

df_fin = pd.read_csv(DATA_DIR / 'WB_ES_T_FIN16.csv')
fin_vals = df_fin[
    (df_fin['REF_AREA'].isin(TARGET_COUNTRIES)) &
    (df_fin['COMP_BREAKDOWN_1'] == '_T') &
    (df_fin['COMP_BREAKDOWN_2'] == '_T') &
    (df_fin['COMP_BREAKDOWN_3'] == '_T')
]['OBS_VALUE']

# Calibration outputs
GROWTH_MEDIAN = float(growth_vals.median())   #  0.2%
GROWTH_P25    = float(growth_vals.quantile(0.25))  # -10.2%
GROWTH_P75    = float(growth_vals.quantile(0.75))  #  5.6%
FIN_CONSTRAINT_MEDIAN = float(fin_vals.median())   # 33.1%

print(f'WB calibration loaded:')
print(f'  Growth median={GROWTH_MEDIAN:.1f}%, P25={GROWTH_P25:.1f}%, P75={GROWTH_P75:.1f}%')
print(f'  Finance constraint median={FIN_CONSTRAINT_MEDIAN:.1f}%')
print()

# ── Config ────────────────────────────────────────────────────────────────────
np.random.seed(42)

N = 100
REPORTING_YEARS     = [2019, 2020, 2021]
MIN_YEARS_OPERATING = 3

COUNTRIES = {
    'Nigeria':      {'currency': 'NGN', 'fx': 1550},
    'Kenya':        {'currency': 'KES', 'fx': 130},
    'Ghana':        {'currency': 'GHS', 'fx': 12},
    'South Africa': {'currency': 'ZAR', 'fx': 19},
    'Ethiopia':     {'currency': 'ETB', 'fx': 57},
    'Rwanda':       {'currency': 'RWF', 'fx': 1200},
    'Tanzania':     {'currency': 'TZS', 'fx': 2500},
    'Uganda':       {'currency': 'UGX', 'fx': 3750},
    'Senegal':      {'currency': 'XOF', 'fx': 600},
    'Egypt':        {'currency': 'EGP', 'fx': 31},
}

SECTORS = ['Fintech', 'Agribusiness', 'Energy', 'Logistics',
           'Healthcare', 'Manufacturing', 'Retail']

COMPANY_NAMES = [
    'Abacus Capital Partners', 'Savanna Growth Fund', 'Meridian Agri Holdings',
    'Kibo Energy Solutions', 'Rift Valley Logistics', 'Nile Tech Ventures',
    'Baobab Financial Services', 'Serengeti Retail Group', 'Atlas Manufacturing Co',
    'Horizon Healthcare Ltd', 'Cascade Fintech', 'Delta Agri Exports',
    'Ember Energy Africa', 'Focal Logistics Group', 'Gateway Retail Africa',
    'Harambee Capital', 'Ivory Coast Ventures', 'Jua Kali Manufacturing',
    'Kilimanjaro Holdings', 'Lakeshore Financial', 'Maisha Health Systems',
    'Nairobi Tech Hub', 'Orbit Agribusiness', 'Pantheon Logistics',
    'Quartz Energy Solutions', 'River Basin Retail', 'Sahel Manufacturing',
    'Tanganyika Capital', 'Ubuntu Financial Group', 'Volta Energy Partners',
    'Wangari Agri Ltd', 'Xcel Logistics Africa', 'Yetu Fintech Solutions',
    'Zambezi Holdings', 'Acacia Capital Group', 'Boma Retail Chain',
    'Crater Lake Energy', 'Dune Manufacturing', 'Equator Healthcare',
    'Flame Tree Ventures', 'Garnet Agribusiness', 'Highveld Capital',
    'Indigo Logistics', 'Jade Financial Africa', 'Kalahari Energy Co',
    'Limpopo Manufacturing', 'Mara Tech Ventures', 'Namib Retail Group',
    'Oasis Healthcare Ltd', 'Prism Capital Africa', 'Savanna Fintech',
    'Thorn Tree Energy', 'Ubuntu Agri Co', 'Virunga Logistics',
    'Waterberg Holdings', 'Xenon Healthcare', 'Yellow River Retail',
    'Zara Manufacturing', 'Apex Fintech Nigeria', 'Benue Agri Partners',
    'Cape Solar Energy', 'Dakar Logistics Hub', 'Eastern Star Healthcare',
    'Frontline Capital', 'Golden Gate Agri', 'Highland Energy Co',
    'Ibadan Tech Ventures', 'Jomo Capital Partners', 'Kinshasa Manufacturing',
    'Lusaka Financial', 'Mombasa Retail Group', 'Northern Agri Holdings',
    'Onyx Energy Africa', 'Palm Capital Group', 'Quantum Fintech',
    'Rift Energy Solutions', 'Serval Logistics', 'Tamu Healthcare',
    'Union Capital Africa', 'Valley Agri Co', 'Westgate Fintech',
    'Xanadu Manufacturing', 'Yola Energy Partners', 'Zenith Logistics Africa',
    'Afri Capital Holdings', 'Bright Future Agri', 'Crown Energy Nigeria',
    'Delta Fintech Hub', 'Eagle Logistics Co', 'Fola Healthcare Ltd',
    'Grand Agri Partners', 'Harvest Energy', 'Inno Tech Africa',
    'Jungle Capital Group', 'Kente Manufacturing', 'Lagos Fintech Corp',
    'Moja Healthcare', 'Nova Agri Solutions', 'Open Energy Africa',
    'Peak Logistics', 'Quest Capital Partners', 'Rapid Fintech Nigeria',
]

# Missing field options for Partial submissions
MISSING_OPTIONS = [
    ['total_debt', 'total_equity'],
    ['operating_expenses'],
    ['finance_costs'],
    ['prior_year_revenue'],
]

# Document reference pools — realistic African SME audit doc names
CLEAN_DOCS = [
    'audited_accounts_{year}.pdf',
    'annual_report_{year}.pdf',
    'financial_statements_{year}.pdf',
    'audited_financials_{year}.pdf',
]
PRIOR_DOCS = [
    'audited_accounts_{year}.pdf',
    'annual_report_{year}.pdf',
    'financial_statements_{year}.pdf',
]
REG_DOCS = [
    'certificate_of_incorporation.pdf',
    'company_registration.pdf',
    'cac_certificate.pdf',
    'business_registration.pdf',
]

# Submission Anomaly seeding — 9 companies, indices 0-indexed
# These companies upload the same document in multiple fields (income statement
# and balance sheet both reference the same file) under an unaudited status.
# Gate 2 (submission integrity) detects this pattern as a potential anomaly.
# Seeded to be ~9% of the pipeline — consistent with realistic pipeline variance.
ANOMALY_INDICES = {2, 7, 17, 18, 19, 23, 24, 28, 31}

# ── Archetype distribution ────────────────────────────────────────────────────
# Calibrated to WB data: most firms have low/negative growth, few are stars.
# Finance constraint median (33.1%) calibrates partial/incomplete split.
archetypes = (
    ['qualified_star'] * 18 +   # clears all 4 signals
    ['scale_up']       * 15 +   # high growth, negative EBITDA
    ['mature_pillar']  * 14 +   # steady revenue, high debt
    ['semi_qualified'] * 20 +   # clears 2–3 signals
    ['unqualified']    * 16 +   # clears 0–1 signals
    ['deferred']       * 17     # < 3 years operating history
)
np.random.shuffle(archetypes)

# Separate RNG for document block — keeps financial profile seed clean
doc_rng = np.random.default_rng(seed=77)

# ── Generation loop ───────────────────────────────────────────────────────────
country_list = list(COUNTRIES.keys())
generated    = []

for i in range(N):
    archetype = archetypes[i]
    company   = COMPANY_NAMES[i]
    sub_id    = f'AF{str(i + 1).zfill(3)}'
    country   = np.random.choice(country_list)
    cinfo     = COUNTRIES[country]
    sector    = np.random.choice(SECTORS)
    rep_year  = int(np.random.choice(REPORTING_YEARS))
    sub_date  = f'{rep_year + 1}-{np.random.randint(1, 6):02d}-{np.random.randint(1, 28):02d}'
    reg_num   = f'RC-{np.random.randint(100000, 999999)}'

    # Founding year — deferred companies have < 3 years operating history
    years_operating = (
        int(np.random.choice([0, 1, 2]))
        if archetype == 'deferred'
        else int(np.random.randint(3, 15))
    )
    year_founded = rep_year - years_operating

    # ── Revenue (power-law, USD millions) ──
    # Distribution skewed to reflect WB finding that most firms are small
    if archetype == 'qualified_star':
        rev_usd = round(min(np.random.pareto(1.5) * 1.5 + 1.5, 30.0), 3)
    elif archetype == 'scale_up':
        rev_usd = round(min(np.random.pareto(2.0) * 0.8 + 0.5, 10.0), 3)
    elif archetype == 'mature_pillar':
        rev_usd = round(min(np.random.pareto(1.2) * 2.0 + 2.0, 25.0), 3)
    elif archetype == 'semi_qualified':
        rev_usd = round(min(np.random.pareto(2.5) * 0.6 + 0.8, 8.0), 3)
    elif archetype == 'unqualified':
        rev_usd = round(np.random.uniform(0.05, 0.95), 3)
    else:  # deferred
        rev_usd = round(np.random.uniform(0.1, 2.0), 3)

    fx        = cinfo['fx']
    rev_local = round(rev_usd * fx * 1_000_000)

    # ── Prior year revenue (growth calibrated to WB ranges) ──
    if archetype == 'qualified_star':
        growth_pct = round(np.random.uniform(10.0, 20.0), 1)
    elif archetype == 'scale_up':
        growth_pct = round(np.random.uniform(20.0, 80.0), 1)
    elif archetype == 'mature_pillar':
        growth_pct = round(np.random.uniform(GROWTH_P25, GROWTH_P75), 1)
    elif archetype == 'semi_qualified':
        growth_pct = round(np.random.uniform(GROWTH_P25, 12.0), 1)
    elif archetype == 'unqualified':
        growth_pct = round(np.random.uniform(-25.0, GROWTH_MEDIAN), 1)
    else:
        growth_pct = None  # deferred — no prior year

    prior_rev_local = (
        round(rev_local / (1 + growth_pct / 100))
        if growth_pct is not None else None
    )
    prior_rep_year = rep_year - 1

    # ── Income statement ──
    if archetype == 'qualified_star':
        gm, opex_r = np.random.uniform(0.40, 0.60), np.random.uniform(0.20, 0.30)
    elif archetype == 'scale_up':
        gm, opex_r = np.random.uniform(0.35, 0.55), np.random.uniform(0.45, 0.70)
    elif archetype == 'mature_pillar':
        gm, opex_r = np.random.uniform(0.45, 0.65), np.random.uniform(0.25, 0.38)
    elif archetype == 'semi_qualified':
        gm, opex_r = np.random.uniform(0.30, 0.50), np.random.uniform(0.25, 0.42)
    elif archetype == 'unqualified':
        gm, opex_r = np.random.uniform(0.15, 0.35), np.random.uniform(0.30, 0.55)
    else:
        gm, opex_r = np.random.uniform(0.20, 0.50), np.random.uniform(0.25, 0.50)

    cos_local      = round(rev_local * (1 - gm))
    gp_local       = rev_local - cos_local
    opex_local     = round(rev_local * opex_r)
    ebitda_local   = gp_local - opex_local
    fin_cost_local = round(rev_local * np.random.uniform(0.04, 0.15))
    pbt_local      = ebitda_local - fin_cost_local

    # ── Balance sheet (D/E ratio per archetype) ──
    if archetype == 'qualified_star':
        d2e = round(np.random.uniform(0.3, 1.8), 2)
    elif archetype == 'scale_up':
        d2e = round(np.random.uniform(0.8, 2.8), 2)
    elif archetype == 'mature_pillar':
        d2e = round(np.random.uniform(2.2, 4.5), 2)
    elif archetype == 'semi_qualified':
        d2e = round(np.random.uniform(1.0, 3.2), 2)
    elif archetype == 'unqualified':
        d2e = round(np.random.uniform(2.8, 6.5), 2)
    else:
        d2e = round(np.random.uniform(0.5, 3.0), 2)

    equity_local = round(rev_local * np.random.uniform(0.3, 0.8))
    debt_local   = round(equity_local * d2e)

    # ── Submission status ──
    # Completeness split calibrated to WB finance constraint median (33.1%):
    #   50% Validated, 33% Partial, 17% Incomplete (for non-deferred)
    if archetype == 'deferred':
        status        = 'Deferred'
        completeness  = None
        missing       = []
        notes         = (
            f'Company incorporated in {year_founded}. '
            f'Insufficient operating history — minimum {MIN_YEARS_OPERATING} years required. '
            f'Resubmit when eligible.'
        )
        audit_status     = 'Audited'
        ebitda_submitted = ebitda_local

    else:
        q = np.random.random()

        if q < 0.50:
            status       = 'Validated'
            completeness = round(np.random.uniform(85, 100), 1)
            missing      = []
            notes        = 'All figures reconciled. EBITDA confirmed against audited accounts.'
            audit_status = 'Audited'
            # 8% chance of minor EBITDA reconciliation variance
            if np.random.random() < 0.08:
                ebitda_submitted = round(ebitda_local * np.random.uniform(1.06, 1.12))
                notes = 'Minor EBITDA reconciliation variance detected. Flagged for reviewer check.'
            else:
                ebitda_submitted = ebitda_local

        elif q < 0.83:
            status       = 'Partial'
            completeness = round(np.random.uniform(55, 80), 1)
            missing_idx  = np.random.randint(0, len(MISSING_OPTIONS))
            missing      = MISSING_OPTIONS[missing_idx]
            notes        = f'Submission incomplete. Missing: {", ".join(missing)}. Requested from company.'
            audit_status = np.random.choice(['Audited', 'Management Accounts'], p=[0.6, 0.4])
            ebitda_submitted = ebitda_local
            if 'total_debt' in missing:
                debt_local = None; d2e = None
            if 'operating_expenses' in missing:
                opex_local = None; ebitda_local = None; ebitda_submitted = None
            if 'finance_costs' in missing:
                fin_cost_local = None; pbt_local = None
            if 'prior_year_revenue' in missing:
                prior_rev_local = None; growth_pct = None

        else:
            status           = 'Incomplete'
            completeness     = round(np.random.uniform(20, 50), 1)
            missing          = ['total_debt', 'total_equity', 'operating_expenses']
            notes            = 'Critical fields missing. Cannot proceed to screening. Follow-up required.'
            audit_status     = np.random.choice(['Unaudited', 'Management Accounts'])
            debt_local       = None; d2e = None
            opex_local       = None; ebitda_local = None; ebitda_submitted = None

    # ── Document references ──
    # Anomaly companies upload the same file in multiple required fields
    is_anomaly = i in ANOMALY_INDICES
    if is_anomaly:
        dup_doc = f'company_documents_{rep_year}.pdf'
        documents = {
            'income_statement_ref':    dup_doc,
            'balance_sheet_ref':       dup_doc,
            'prior_year_accounts_ref': dup_doc if doc_rng.random() < 0.6
                                       else f'accounts_{rep_year - 1}.pdf',
            'registration_doc_ref':    str(doc_rng.choice(REG_DOCS)),
        }
    else:
        inc_doc     = doc_rng.choice(CLEAN_DOCS).format(year=rep_year)
        bal_options = [d.format(year=rep_year) for d in CLEAN_DOCS if d.format(year=rep_year) != inc_doc]
        bal_doc     = str(doc_rng.choice(bal_options)) if bal_options else f'balance_sheet_{rep_year}.pdf'
        prior_doc   = doc_rng.choice(PRIOR_DOCS).format(year=rep_year - 1)
        documents   = {
            'income_statement_ref':    inc_doc,
            'balance_sheet_ref':       bal_doc,
            'prior_year_accounts_ref': prior_doc,
            'registration_doc_ref':    str(doc_rng.choice(REG_DOCS)),
        }

    # ── Build JSON profile ──
    profile = {
        'submission_id':     sub_id,
        'submission_date':   sub_date,
        'submission_status': status,

        'company': {
            'name':                company,
            'country':             country,
            'reporting_currency':  cinfo['currency'],
            'fx_rate_to_usd':      fx,
            'sector':              sector,
            'registration_number': reg_num,
            'year_founded':        year_founded,
        },

        'financials': {
            'reporting_year':     rep_year,
            'audit_status':       audit_status,
            'revenue':            rev_local,
            'cost_of_sales':      cos_local,
            'gross_profit':       gp_local,
            'operating_expenses': opex_local,
            'ebitda':             ebitda_submitted,
            'finance_costs':      fin_cost_local,
            'profit_before_tax':  pbt_local,
            'total_debt':         debt_local,
            'total_equity':       equity_local,
        },

        'prior_year_financials': {
            'reporting_year': prior_rep_year,
            'revenue':        prior_rev_local,
            'audit_status':   audit_status,
        } if archetype != 'deferred' else None,

        'data_quality': {
            'completeness_score': completeness,
            'missing_fields':     missing,
            'reviewer_notes':     notes,
        },

        'designated_contact': {
            'role': 'CEO',
        },

        'documents': documents,

        '_meta': {
            'archetype':          archetype,
            'years_operating':    years_operating,
            'submission_anomaly': is_anomaly,
        },
    }

    with open(PROFILES_DIR / f'{sub_id}.json', 'w') as f:
        json.dump(profile, f, indent=2)

    generated.append({
        'submission_id': sub_id,
        'archetype':     archetype,
        'status':        status,
        'country':       country,
    })

# ── Summary ───────────────────────────────────────────────────────────────────
df_gen = pd.DataFrame(generated)
print(f'Generated {N} JSON profiles → company_profiles/')
print()
print('Archetype distribution:')
print(df_gen['archetype'].value_counts().to_string())
print()
print('Submission status distribution:')
print(df_gen['status'].value_counts().to_string())
print()
print('Country distribution:')
print(df_gen['country'].value_counts().to_string())
print()
print('Next step: run pipeline/extract_and_validate.py')
