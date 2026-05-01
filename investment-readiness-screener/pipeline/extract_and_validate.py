"""
Investment Readiness Screener — Phase 2: Extraction & Validation Pipeline
=========================================================================
Crystal Olisa · Operations Generalist

Gate structure:

  Gate 1   — Operational maturity
             Condition: reporting_year − year_founded < 3
             Action:    Deferred — exit pipeline
             Rationale: EBITDA from fewer than three years of operations is not
                        a reliable signal. The company has not demonstrated
                        sufficient operating history for investment consideration.

  Gate 2   — Submission integrity (non-blocking)
             Condition: duplicate document references across fields + unaudited
                        or management accounts status
             Action:    ⚑ Submission Anomaly flag — internal only, proceed
             Rationale: A founder who uploads the same document in multiple
                        fields to satisfy intake requirements is signalling
                        they do not have the required documentation. Combined
                        with an unaudited status, this warrants reviewer
                        scrutiny before any pipeline time is spent.

  Gate 3   — Financial history
             Condition: prior year revenue absent from submission
             Action:    Deferred — exit pipeline
             Rationale: Year-on-year growth cannot be calculated from a single
                        year of accounts. All four criteria must be assessable
                        for an investment evaluation to proceed. This is not a
                        soft flag — a company cannot be evaluated as strong or
                        weak on three out of four criteria. Each criterion is
                        individually necessary; the others do not compensate
                        for its absence.

  Gate 4   — EBITDA reconciliation (non-blocking)
             Condition: submitted EBITDA vs derived (GP − opex) variance > 5%
             Action:    Flag — proceed with reviewer note
             Rationale: Submitted EBITDA is cross-checked against derived.
                        Variance may reflect a legitimate accounting treatment.
                        Flagged for reviewer verification before advancing.

  Gate 5   — Standardisation and metric derivation
             Action:    Convert local currency to USD millions. Calculate
                        EBITDA margin, YoY growth, debt-to-equity.

Founder-facing outcomes (three only):
  Advance  — all four criteria met
  Decline  — one or more criteria not met
  Deferred — Gate 1 or Gate 3 failure

Internal-only flags:
  ⚑ Submission Anomaly — duplicate document references + unaudited status
"""

import json
import pandas as pd
from pathlib import Path

PROFILES_DIR        = Path(__file__).parent.parent / 'company_profiles'
OUTPUT_PATH         = Path(__file__).parent.parent / 'data' / 'screening_results.csv'
EBITDA_TOLERANCE    = 0.05
MIN_YEARS_OPERATING = 3
UNAUDITED_STATUSES  = {'Unaudited', 'Management Accounts'}

THRESHOLDS = {
    'revenue_usd_millions': {'advance': 1.5,  'review': 1.0,  'higher': True},
    'ebitda_margin_pct':    {'advance': 15.0, 'review': 5.0,  'higher': True},
    'revenue_growth_pct':   {'advance': 10.0, 'review': 3.0,  'higher': True},
    'debt_to_equity':       {'advance': 2.0,  'review': 3.0,  'higher': False},
}

# ── Helpers ────────────────────────────────────────────────────────────────

def safe_div(n, d):
    if n is None or d is None or d == 0: return None
    return n / d

def to_usd_millions(local, fx):
    if local is None or fx is None or fx == 0: return None
    return round(local / (fx * 1_000_000), 4)

def check_ebitda_reconciliation(submitted, gp, opex, tol=EBITDA_TOLERANCE):
    if None in (submitted, gp, opex): return False, None
    derived = gp - opex
    if derived == 0: return False, None
    var = abs(submitted - derived) / abs(derived)
    return var > tol, round(var * 100, 2)

# ── Gates ──────────────────────────────────────────────────────────────────

def gate_1_maturity(profile):
    yr_founded = profile['company'].get('year_founded')
    rep_year   = profile['financials'].get('reporting_year')
    if yr_founded is None or rep_year is None:
        return False, 'gate_1', 'Founding year or reporting year missing.'
    years = rep_year - yr_founded
    if years < MIN_YEARS_OPERATING:
        return False, 'gate_1', (
            f'Company incorporated in {yr_founded}. '
            f'{years} year(s) of operating history — minimum {MIN_YEARS_OPERATING} required. '
            f'Resubmit when eligible.'
        )
    return True, None, None


def gate_2_anomaly(profile):
    docs  = profile.get('documents', {})
    audit = profile['financials'].get('audit_status', '')
    if not docs: return False, None
    doc_refs = [v for v in docs.values() if v]
    inc = docs.get('income_statement_ref')
    bal = docs.get('balance_sheet_ref')
    critical_dup   = inc and bal and inc == bal
    has_duplicates = len(doc_refs) > len(set(doc_refs))
    is_unaudited   = audit in UNAUDITED_STATUSES
    if critical_dup and is_unaudited:
        return True, (
            f'Duplicate document reference: income statement and balance sheet '
            f'both reference "{inc}". Audit status: {audit}. '
            f'Flagged for reviewer scrutiny before pipeline proceeds.'
        )
    if has_duplicates and is_unaudited:
        dupes = list(set(r for r in doc_refs if doc_refs.count(r) > 1))
        return True, (
            f'Duplicate document references across submission fields: {dupes}. '
            f'Audit status: {audit}. Flagged for reviewer scrutiny.'
        )
    return False, None


def gate_3_financial_history(profile):
    pyfin = profile.get('prior_year_financials') or {}
    prior_rev = pyfin.get('revenue')
    if prior_rev is None:
        rep_year = profile['financials'].get('reporting_year', '—')
        return False, 'gate_3', (
            f'Insufficient financial history. A minimum of two consecutive years '
            f'of audited accounts is required to assess year-on-year growth. '
            f'Only one year of accounts ({rep_year}) was provided. '
            f'Resubmit when your accounts reflect at least two full financial years.'
        )
    return True, None, None


def gate_4_reconciliation(profile):
    fin = profile['financials']
    flagged, var_pct = check_ebitda_reconciliation(
        fin.get('ebitda'), fin.get('gross_profit'), fin.get('operating_expenses'))
    if flagged:
        return True, var_pct, (
            f'EBITDA reconciliation variance: {var_pct}% — '
            f'submitted figure does not match derived (gross profit − operating expenses). '
            f'Flagged for reviewer check.'
        )
    return False, var_pct, None


def gate_5_metrics(profile):
    fin   = profile['financials']
    pyfin = profile.get('prior_year_financials') or {}
    fx    = profile['company'].get('fx_rate_to_usd', 1)
    rev_local  = fin.get('revenue')
    prior_rev  = pyfin.get('revenue')
    gp         = fin.get('gross_profit')
    opex       = fin.get('operating_expenses')
    ebitda_sub = fin.get('ebitda')
    ebitda_use = (gp - opex) if gp is not None and opex is not None else ebitda_sub
    ebitda_margin = round(safe_div(ebitda_use, rev_local) * 100, 2) \
                    if safe_div(ebitda_use, rev_local) is not None else None
    growth = round((rev_local - prior_rev) / prior_rev * 100, 2) \
             if rev_local and prior_rev and prior_rev != 0 else None
    d2e = safe_div(fin.get('total_debt'), fin.get('total_equity'))
    d2e = round(d2e, 3) if d2e is not None else None
    return {
        'revenue_usd_millions': to_usd_millions(rev_local, fx),
        'ebitda_margin_pct':    ebitda_margin,
        'revenue_growth_pct':   growth,
        'debt_to_equity':       d2e,
    }

# ── Screening ──────────────────────────────────────────────────────────────

def score_criterion(val, key):
    if val is None: return None
    t = THRESHOLDS[key]
    if t['higher']:
        if val >= t['advance']: return 'advance'
        if val >= t['review']:  return 'review'
        return 'decline'
    else:
        if val <= t['advance']: return 'advance'
        if val <= t['review']:  return 'review'
        return 'decline'


def assign_investment_flag(metrics):
    """
    All four criteria must be assessable and must clear the Advance threshold.
    No partial assessments. No exceptions.
    A company cannot be evaluated as investable on three out of four criteria.
    """
    scores = {k: score_criterion(metrics.get(k), k) for k in THRESHOLDS}
    available = [s for s in scores.values() if s is not None]

    # All four must be present — Gate 3 should have caught missing growth,
    # but this is the final check
    if len(available) < 4:
        return 'Decline', scores

    # All four must be Advance
    if all(s == 'advance' for s in available):
        return 'Advance', scores

    return 'Decline', scores

# ── Main pipeline ──────────────────────────────────────────────────────────

def run_pipeline():
    profile_files = sorted(PROFILES_DIR.glob('*.json'))
    print(f'Found {len(profile_files)} company profiles\n')

    records = []
    counts = {
        'gate_1': 0, 'gate_2': 0, 'gate_3': 0,
        'gate_4': 0, 'advance': 0, 'decline': 0,
    }

    for path in profile_files:
        with open(path) as f:
            profile = json.load(f)

        sub_id      = profile['submission_id']
        company     = profile['company']['name']
        country     = profile['company']['country']
        currency    = profile['company']['reporting_currency']
        fx          = profile['company']['fx_rate_to_usd']
        sector      = profile['company']['sector']
        rep_year    = profile['financials']['reporting_year']
        founded     = profile['company']['year_founded']
        audit       = profile['financials']['audit_status']
        sub_status  = profile['submission_status']
        dq          = profile.get('data_quality', {})
        docs        = profile.get('documents', {})

        pipeline_status = None
        pipeline_note   = None
        deferred_reason = None
        anomaly_flag    = False
        anomaly_reason  = None
        ebitda_flag     = False
        ebitda_var      = None
        metrics         = {}
        scores          = {}
        inv_flag        = None

        # Gate 1 — Operational maturity
        g1_ok, _, g1_note = gate_1_maturity(profile)
        if not g1_ok:
            pipeline_status = 'Deferred'
            pipeline_note   = g1_note
            deferred_reason = 'operating_history'
            inv_flag        = 'Deferred'
            counts['gate_1'] += 1

        else:
            # Gate 2 — Submission integrity (non-blocking)
            anomaly_flag, anomaly_reason = gate_2_anomaly(profile)
            if anomaly_flag:
                counts['gate_2'] += 1

            # Gate 3 — Financial history
            g3_ok, _, g3_note = gate_3_financial_history(profile)
            if not g3_ok:
                pipeline_status = 'Deferred'
                pipeline_note   = g3_note
                deferred_reason = 'financial_history'
                inv_flag        = 'Deferred'
                counts['gate_3'] += 1

            else:
                # Gate 4 — EBITDA reconciliation (non-blocking)
                ebitda_flag, ebitda_var, g4_note = gate_4_reconciliation(profile)
                if ebitda_flag:
                    counts['gate_4'] += 1
                    pipeline_note = g4_note

                # Gate 5 — Derive metrics and screen
                metrics  = gate_5_metrics(profile)
                inv_flag, scores = assign_investment_flag(metrics)
                pipeline_status = 'Validated'

                if inv_flag == 'Advance': counts['advance'] += 1
                else: counts['decline'] += 1

        records.append({
            'submission_id':        sub_id,
            'company_name':         company,
            'country':              country,
            'reporting_currency':   currency,
            'fx_rate_to_usd':       fx,
            'sector':               sector,
            'reporting_year':       rep_year,
            'year_founded':         founded,
            'years_operating':      rep_year - founded,
            'audit_status':         audit,
            'submission_status':    sub_status,
            'pipeline_status':      pipeline_status,
            'investment_flag':      inv_flag,
            'deferred_reason':      deferred_reason,
            'submission_anomaly':   anomaly_flag,
            'anomaly_reason':       anomaly_reason,
            'pipeline_note':        pipeline_note,
            'ebitda_recon_flag':    ebitda_flag,
            'ebitda_variance_pct':  ebitda_var,
            'completeness_score':   dq.get('completeness_score'),
            'doc_income_statement': docs.get('income_statement_ref'),
            'doc_balance_sheet':    docs.get('balance_sheet_ref'),
            'doc_prior_year':       docs.get('prior_year_accounts_ref'),
            'doc_registration':     docs.get('registration_doc_ref'),
            'revenue_local':        profile['financials'].get('revenue'),
            'ebitda_local':         profile['financials'].get('ebitda'),
            'total_debt_local':     profile['financials'].get('total_debt'),
            'total_equity_local':   profile['financials'].get('total_equity'),
            'revenue_usd_millions': metrics.get('revenue_usd_millions'),
            'ebitda_margin_pct':    metrics.get('ebitda_margin_pct'),
            'revenue_growth_pct':   metrics.get('revenue_growth_pct'),
            'debt_to_equity':       metrics.get('debt_to_equity'),
            'rev_score':            scores.get('revenue_usd_millions'),
            'ebitda_score':         scores.get('ebitda_margin_pct'),
            'growth_score':         scores.get('revenue_growth_pct'),
            'd2e_score':            scores.get('debt_to_equity'),
        })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_PATH, index=False)

    print('═' * 60)
    print('PIPELINE SUMMARY')
    print('═' * 60)
    print(f'Total processed:                    {len(df)}')
    print(f'Gate 1 — Deferred (maturity):       {counts["gate_1"]}')
    print(f'Gate 2 — Anomaly flagged:           {counts["gate_2"]} (internal, proceed)')
    print(f'Gate 3 — Deferred (fin history):    {counts["gate_3"]}')
    print(f'Gate 4 — EBITDA flagged:            {counts["gate_4"]} (proceed with note)')
    print()
    print('Investment flag distribution:')
    print(df['investment_flag'].value_counts().to_string())
    print()
    print('Deferred breakdown:')
    print(df[df['investment_flag']=='Deferred']['deferred_reason'].value_counts().to_string())
    print()
    print('Submission anomalies (internal):')
    anom = df[df['submission_anomaly']==True][['submission_id','company_name','audit_status','investment_flag']]
    print(anom.to_string(index=False))
    print(f'\nOutput: {OUTPUT_PATH}')
    return df


if __name__ == '__main__':
    df = run_pipeline()
