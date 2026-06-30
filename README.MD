# PH Corporate Finance & FP&A

> **An end-to-end Kimball data warehouse built on Snowflake + dbt + Airflow — purpose-built for Filipino corporate FP&A: actual vs. budget variance, consolidated P&L, rolling forecasts, cash flow statements, AP/AR working capital, and intercompany-eliminated group consolidation across a multi-subsidiary group.**

![ETL_PH-Multi-Subsidiary-Enterprise-Data-Warehouse](https://tdhghaslnufgtzjybhhf.supabase.co/storage/v1/object/public/content/ETL%20Engineer%20Portfoilo/ph_corporate_fpna_analytics.png)

---

## What This Is

A production-grade FP&A that mirrors real-world corporate finance infrastructure — dimensional modeling on Snowflake, transformation pipelines in dbt, orchestration via Airflow, and a reporting layer designed to answer CFO-level questions in seconds.

This is not a tutorial project. Every architectural decision here reflects a deliberate tradeoff made for an FP&A context specifically: why budget data uses `materialized='table'` instead of incremental, why `dim_scenario` is the dimension that separates this from a basic GL report, why FULL OUTER JOINs matter in variance analysis, why a control table is better than a seed file for period lock status, and why GL sign conventions are normalized once at the dimension level instead of trusted to every downstream SUM.

---

## Tech Stack

| Layer           | Tool                                  | Purpose                                      |
| --------------- | ------------------------------------- | -------------------------------------------- |
| Cloud Warehouse | Snowflake (X-Small, auto-suspend 60s) | Storage + compute                            |
| Transformation  | dbt Core                              | Staging → Dimensions → Facts → Reporting     |
| Orchestration   | Apache Airflow 2.x (TaskFlow API)     | Monthly close pipeline                       |
| Data Packages   | dbt_utils, dbt_expectations           | Surrogate keys + advanced data quality tests |
| BI Layer        | Metabase / Preset                     | Executive dashboards                         |
| Languages       | Python 3, SQL, YAML                   | Scripts, models, config                      |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCE SYSTEMS                                                  │
│  ERP (GL) │ Budget Uploads │ Bank Feeds │ Excel Uploads          │
│  HRIS Roster │ AP/AR Invoices │ Intercompany Postings            │
└─────────────────────────────────────────────────────────────────┘
                              │ Python scripts (PUT + COPY INTO)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BRONZE  (fpna_db.bronze)  — append-only raw CSV ingestion      │
│  raw_gl_actuals │ raw_budget │ raw_forecast │ raw_bank_statements│
│  raw_manual_adjustments │ raw_employee_roster │ raw_ap_ar        │
│  raw_intercompany                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │ dbt staging models (views)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SILVER  (fpna_db.silver)  — cleaned, typed, unified            │
│  stg_gl_actuals (ERP + Excel adjustments merged)                │
│  stg_budget │ stg_forecast │ stg_bank_statements                │
│  stg_employee_roster │ stg_ap_ar │ stg_intercompany              │
└─────────────────────────────────────────────────────────────────┘
                              │ dbt mart models (tables + incremental)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GOLD  (fpna_db.gold)  — Star Schema                            │
│                                                                  │
│  DIMENSIONS          FACT TABLES                                 │
│  dim_date      ───► fct_gl_actuals   (incremental, 12,000 rows) │
│  dim_account   ───► fct_budget       (table, full refresh)      │
│  dim_cost_center──► fct_forecast     (table, full refresh)      │
│  dim_subsidiary───► fct_cash_flow    (incremental)              │
│  dim_scenario  ───► fct_ap_ar        (table, full refresh)      │
│  dim_employee  ───► fct_intercompany (incremental)              │
│                                                                  │
│  REPORTING MARTS                                                 │
│  rpt_variance_analysis      │  rpt_pnl_summary                  │
│  rpt_cash_flow_statement    │  rpt_executive_dashboard          │
│  rpt_forecast_accuracy      │  rpt_cost_center_variance         │
│  rpt_subsidiary_consolidation                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD  — Metabase / Preset                                  │
│  P&L Waterfall │ Variance Heatmap │ Actual vs Budget vs Forecast │
│  Cash Flow Statement │ Subsidiary P&L Comparison                │
│  Forecast Accuracy │ Cost Center Drill-Down │ Group Consolidation│
└─────────────────────────────────────────────────────────────────┘
```

---

## ETL Philosophy

**Kimball (Bottom-Up) + Unix Philosophy + 80/20 Pareto**

The Kimball methodology was chosen deliberately over Data Vault for three reasons:

1. **Business questions are stable.** FP&A analysts always ask the same types of questions: actual vs. budget variance by cost center, P&L by subsidiary, rolling forecast accuracy. The star schema answers all of them without complex query gymnastics.

2. **Conformed dimensions compound value.** `dim_date`, `dim_account`, and `dim_subsidiary` are shared across all six fact tables. Add a new BI report? It inherits every dimension for free.

3. **Speed matters at the CFO level.** A flat star schema on Snowflake returns consolidated P&L in under two seconds. That matters when you're in a board meeting.

Data Vault was explicitly ruled out. The audit requirement is met by keeping bronze GL entries append-only — satellite history tracking would add complexity with zero marginal benefit here.

---

## Data Model — Star Schema

### Fact Tables

| Table              | Grain                                                          | Materialization      | Key Measures                                          |
| ------------------ | -------------------------------------------------------------- | -------------------- | ----------------------------------------------------- |
| `fct_gl_actuals`   | 1 row per GL journal line                                      | Incremental          | `debit_amount`, `credit_amount`, `net_amount_php`     |
| `fct_budget`       | 1 row per account × cost center × subsidiary × month           | Table (full refresh) | `budget_amount_php`                                   |
| `fct_forecast`     | 1 row per account × cost center × subsidiary × month × version | Table (full refresh) | `forecast_amount_php`                                 |
| `fct_cash_flow`    | 1 row per bank transaction                                     | Incremental          | `inflow_php`, `outflow_php`, `net_cash_php`           |
| `fct_ap_ar`        | 1 row per AP/AR invoice                                        | Table (full refresh) | `amount_php`, `signed_amount_php`, `days_outstanding` |
| `fct_intercompany` | 1 row per intercompany posting                                 | Incremental          | `amount_php`                                          |

**Why `fct_budget` is `materialized='table'` (not incremental):** Budget data is static — once the CFO signs off, it doesn't change. Incremental logic would add surrogate key complexity with zero performance benefit. Knowing when _not_ to use incremental is as important as knowing when to use it.

**Why `fct_ap_ar` is `materialized='table'`, not incremental:** Invoice `status` (OPEN/PAID/OVERDUE) changes after the row first lands — an append-only incremental model would keep stale status rows around indefinitely. A full refresh keeps the table honest at the cost of a cheap nightly rebuild.

### Dimension Tables

| Table             | Key Design Decision                                                                                                                                                                                                                                                         |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dim_date`        | `period_status` (OPEN/CLOSED) sourced from `control.period_lock` — a live table, not a static seed. The fiscal calendar _shape_ is a seed; close _status_ is operational.                                                                                                   |
| `dim_account`     | Carries `sign_convention` (-1 for Revenue, +1 for everything else) so every downstream fact and mart can treat Revenue, COGS, OpEx, Finance Cost, and Tax as positive magnitudes and combine them by explicit subtraction instead of guessing GL debit/credit-normal signs. |
| `dim_scenario`    | The dimension that makes this an FP&A platform, not just a GL report. Analysts switch between Actual, Budget, RF1, RF2, RF3 in a single query — no UNION statements needed.                                                                                                 |
| `dim_cost_center` | Carries the full cost center → department → division → subsidiary hierarchy, enabling drill-down from group-level to individual cost centers.                                                                                                                               |
| `dim_subsidiary`  | Supports multi-entity group structures with per-subsidiary reporting currency and an `is_group_entity` flag used in consolidation. Essential for a conglomerate FP&A model.                                                                                                 |
| `dim_employee`    | Headcount and comp roster joined to `dim_cost_center` / `dim_subsidiary`, enabling personnel-cost variance below the cost-center aggregate level.                                                                                                                           |

---

## Key Design Decisions Worth Noting

**1. ERP entries + Excel adjustments unified at staging, not at bronze**

Finance teams always have both sources. Merging them at `stg_gl_actuals` via UNION ALL (not at bronze) keeps the raw sources clean and independently queryable, while presenting a single actuals view downstream. Treating them differently below the staging layer creates reconciliation nightmares.

**2. `rpt_variance_analysis` uses FULL OUTER JOIN**

This is the most common trap that breaks finance dashboards. An INNER JOIN drops accounts that have budget but no actuals (and vice versa) — perfectly valid during the year when some accounts haven't posted yet. The FULL OUTER JOIN ensures every budget line appears in variance reports even before actuals come in, which is how finance teams actually use these reports.

**3. `control.period_lock` is a live table, not a seed**

`ph_fiscal_calendar.csv` defines the fiscal calendar shape — which months belong to which quarter. That's static calendar configuration. But whether a period is OPEN or CLOSED is an operational decision made each month-end by the finance controller. These two concerns belong in separate places. Merging them back into one seed file would mean re-seeding every time a period closes. (The singular test below reads `closed_date` from `control.period_lock` for exactly this reason — not from the static seed.)

**4. Incremental models use `_loaded_at` as the watermark**

Rather than relying on `posting_date` (which can be backdated for adjustments and accruals), the watermark is `_loaded_at` — the timestamp of when the record arrived in bronze. This means late-arriving entries and month-end accruals are always picked up on the next run, regardless of what date they were posted to.

**5. `assert_budget_equals_actuals_period` enforces financial close discipline**

This singular dbt test flags GL postings to already-closed periods. In practice, this is one of the most common data quality failures in corporate finance — someone posts a January accrual in March, long after January was closed. The test catches it automatically and fails the pipeline, forcing a conscious decision about whether to reopen the period.

**6. `dim_account.sign_convention` is normalized once, applied once**

The GL stores Revenue credit-normal (negative `net_amount`) and COGS/OpEx/Finance Cost/Tax debit-normal (positive `net_amount`) — standard double-entry bookkeeping. `dim_account.sign_convention` flips Revenue to `-1` so it lands positive, leaving expense-type accounts at `+1` since they're already positive. `fct_gl_actuals.net_amount_php` applies this multiplier exactly once. Every reporting mart downstream (`rpt_pnl_summary`, `rpt_executive_dashboard`) can then trust that Revenue, COGS, OpEx, Finance Cost, and Tax all arrive as positive magnitudes, and computes `gross_profit`, `ebitda`, and `net_income` by **explicit subtraction** rather than blind `SUM()`s across account types — the latter silently produces inverted P&L figures if the sign isn't normalized upstream.

**7. Intercompany eliminations only adjust revenue, not net income**

`fct_intercompany` captures shared-service charge-outs, intercompany loans, and management fees between subsidiaries. At the standalone subsidiary level, these show up as revenue for the charging entity and expense for the receiving entity — both real GL postings. At the GROUP level they're a wash: one subsidiary's expense is another's revenue, so they net to zero in aggregate net income automatically. `rpt_subsidiary_consolidation` only needs to subtract the intercompany total from consolidated _revenue_ to avoid double-counting; `net_income` is left untouched.

---

## Source Data Simulation

Eight Python scripts generate realistic Philippine corporate finance data:

| Script                           | Output                       | Volume                                                                   |
| -------------------------------- | ---------------------------- | ------------------------------------------------------------------------ |
| `generate_gl_actuals.py`         | `raw_gl_actuals.csv`         | 12,000 GL lines (24 months × 500 entries)                                |
| `generate_budget.py`             | `raw_annual_budget.csv`      | FY2024 + FY2025, all accounts × cost centers × subsidiaries              |
| `generate_forecast.py`           | `raw_revised_forecast.csv`   | RF1, RF2, RF3 rolling forecast versions                                  |
| `generate_bank_statements.py`    | `raw_bank_statements.csv`    | 18 months, 6 subsidiary bank accounts (BDO, BPI, Metrobank, LandBank)    |
| `generate_manual_adjustments.py` | `raw_manual_adjustments.csv` | 720 month-end Excel adjustments (accruals, reversals, reclassifications) |
| `generate_employee_roster.py`    | `raw_employee_roster.csv`    | ~400 employees across 10 cost centers and 5 subsidiaries                 |
| `generate_ap_ar.py`              | `raw_ap_ar.csv`              | 24 months, ~20–60 AP/AR invoices per month                               |
| `generate_intercompany.py`       | `raw_intercompany.csv`       | 24 months, ~5–15 intercompany postings per month across 5 subsidiaries   |

Data is seeded with `random.seed(42)` for reproducibility. Philippine locale details (bank names, cost center codes, subsidiary structures) are modeled to reflect actual corporate finance structures in the Philippines.

---

## dbt Project Structure

```
fpna_dbt/
├── models/
│   ├── staging/           # Views over bronze — typed, cleaned, deduplicated
│   │   ├── sources.yml    # Source tests: not_null, unique, accepted_values
│   │   ├── stg_gl_actuals.sql        # Merges ERP + Excel adjustments
│   │   ├── stg_budget.sql
│   │   ├── stg_forecast.sql
│   │   ├── stg_bank_statements.sql
│   │   ├── stg_manual_adjustments.sql
│   │   ├── stg_employee_roster.sql
│   │   ├── stg_ap_ar.sql
│   │   └── stg_intercompany.sql
│   └── marts/
│       ├── core/          # Dimensions (table) + Facts (table or incremental)
│       │   ├── schema.yml         # Data quality tests on all core models
│       │   ├── dim_date.sql       # Joins fiscal calendar + period_lock
│       │   ├── dim_account.sql    # GL accounts + P&L sign convention
│       │   ├── dim_cost_center.sql
│       │   ├── dim_subsidiary.sql
│       │   ├── dim_scenario.sql   # Actual / Budget / Revised Forecast
│       │   ├── dim_employee.sql
│       │   ├── fct_gl_actuals.sql
│       │   ├── fct_budget.sql
│       │   ├── fct_forecast.sql
│       │   ├── fct_cash_flow.sql
│       │   ├── fct_ap_ar.sql
│       │   └── fct_intercompany.sql
│       └── reporting/     # Pre-aggregated marts consumed by BI tools
│           ├── schema.yml
│           ├── rpt_variance_analysis.sql       # Core FP&A deliverable
│           ├── rpt_pnl_summary.sql             # Revenue → GP → EBITDA → NI
│           ├── rpt_cash_flow_statement.sql     # Operating / Investing / Financing
│           ├── rpt_executive_dashboard.sql     # CFO-level KPI rollup
│           ├── rpt_forecast_accuracy.sql       # RF1/RF2/RF3 vs actual
│           ├── rpt_cost_center_variance.sql    # Actual vs Budget by cost center
│           └── rpt_subsidiary_consolidation.sql # GROUP P&L, IC eliminated
└── tests/
    └── assert_budget_equals_actuals_period.sql  # Late posting detection
```

---

## Pipeline Orchestration (Airflow)

**Schedule:** `0 6 1 * *` — 6 AM on the 1st of every month (month-end financial close cycle)

The DAG uses Airflow's TaskFlow API (decorator-based) and runs in two stages:

**Stage 1 — Data generation (parallel)**

All eight source CSV generators run simultaneously. No dependencies between them.

**Stage 2 — Sequential pipeline**

```
[generate_*] → load_init_snowflake → load_bronze → dbt deps
            → dbt seed → dbt run staging → dbt run core
            → dbt run reporting → dbt test
```

`load_init_snowflake` runs `CREATE OR REPLACE` on bronze tables and `CREATE TABLE IF NOT EXISTS` on the control table — fully idempotent regardless of execution order. The DAG is safe to re-run at any point.

---

## Reporting Layer

Eight dashboard views, all sourced from `fpna_db.gold`:

| Dashboard                    | Source Model                   | Answers                                                    |
| ---------------------------- | ------------------------------ | ---------------------------------------------------------- |
| P&L Waterfall                | `rpt_pnl_summary`              | Revenue → Gross Profit → EBITDA → Net Income               |
| Variance Heatmap             | `rpt_variance_analysis`        | Which cost centers are over/under budget?                  |
| Actual vs Budget vs Forecast | `rpt_variance_analysis`        | Are we tracking to plan? Which scenario is closest?        |
| Cash Flow Statement          | `rpt_cash_flow_statement`      | Operating, Investing, Financing cash movement              |
| Subsidiary P&L Comparison    | `rpt_pnl_summary`              | Which entities are performing vs dragging group P&L?       |
| Forecast Accuracy            | `rpt_forecast_accuracy`        | Does RF3 actually beat RF1? Where do forecasts miss most?  |
| Cost Center Drill-Down       | `rpt_cost_center_variance`     | Which department, specifically, is driving the variance?   |
| Group Consolidation          | `rpt_subsidiary_consolidation` | What's the true GROUP P&L after intercompany eliminations? |

---

## Data Quality Layer

**Source tests** (`sources.yml`): `not_null`, `unique`, `accepted_values` on all bronze tables, including the new `raw_employee_roster`, `raw_ap_ar`, and `raw_intercompany`
**Model tests** (`schema.yml`): `unique`, `not_null`, `dbt_expectations.expect_column_values_to_be_between` on all fact and dimension models, plus `accepted_values` on `dim_account.sign_convention` (`-1` or `1`)
**Singular test**: `assert_budget_equals_actuals_period` — fails the pipeline if GL entries are posted to closed periods, checked against `control.period_lock`

---

## 80/20 Delivery Order

The project was scoped to deliver the highest-value outputs first, following Pareto priority:

| Priority   | Deliverable                                                   | Value                             |
| ---------- | ------------------------------------------------------------- | --------------------------------- |
| 1 — Must   | `raw_gl_actuals` + `raw_budget` bronze load                   | Data in warehouse                 |
| 2 — Must   | `stg_gl_actuals` + `stg_budget`                               | Clean, typed actuals and budget   |
| 3 — Must   | `dim_account` + `dim_cost_center` + `dim_date`                | Dimensional foundation            |
| 4 — Must   | `fct_gl_actuals` + `fct_budget` + `rpt_variance_analysis`     | Core FP&A deliverable             |
| 5 — Should | `rpt_pnl_summary` + Metabase P&L dashboard                    | Executive visibility              |
| 6 — Should | `stg_forecast` + `fct_forecast` + `rpt_forecast_accuracy`     | Forecast accuracy                 |
| 7 — Should | `raw_bank_statements` + `fct_cash_flow` + cash flow statement | Liquidity view                    |
| 8 — Nice   | Manual adjustment Excel upload pipeline                       | Month-end close completeness      |
| 9 — Nice   | Period lock enforcement + Airflow monthly DAG                 | Operational discipline            |
| 10 — Nice  | `dim_employee` + `fct_ap_ar` + `rpt_cost_center_variance`     | Headcount + working-capital depth |
| 11 — Nice  | `fct_intercompany` + `rpt_subsidiary_consolidation`           | True GROUP-level consolidation    |

The first four priorities (items 1–4) are what make this an FP&A platform. Everything after is additive.

---

## Repository Structure

```
ph-corporate-fpna/
├── data/
│   ├── erp/            raw_gl_actuals.csv
│   ├── budget/         raw_annual_budget.csv, raw_revised_forecast.csv
│   ├── banking/        raw_bank_statements.csv
│   ├── excel/          raw_manual_adjustments.csv
│   ├── hr/             raw_employee_roster.csv
│   ├── ap_ar/          raw_ap_ar.csv
│   └── intercompany/   raw_intercompany.csv
├── seeds/
│   ├── chart_of_accounts.csv
│   ├── cost_center_hierarchy.csv
│   ├── ph_fiscal_calendar.csv
│   └── fx_rates.csv
├── scripts/
│   ├── generate_*.py               Source data simulation (8 scripts)
│   ├── load_init_snowflake.py      Idempotent DDL setup
│   ├── load_bronze.py              PUT + COPY INTO all tables
│   └── close_period.py             Finance team period close tool
├── fpna_dbt/                       dbt project (staging → core → reporting)
├── dags/
│   └── fpna_etl_dag.py             Airflow monthly pipeline
└── dashboard/
    └── executive_dashboard.json    Metabase export
```

---

## Cost Management

This project runs on a single `X-SMALL` Snowflake warehouse with `AUTO_SUSPEND = 60` seconds. FP&A models are inherently low-frequency — the pipeline runs once per financial close cycle (monthly). Scheduling dbt runs at month-end only avoids burning Snowflake credits on static budget data that hasn't changed.

Estimated monthly Snowflake cost for a full pipeline run: < $1 USD.

---

## About the Design

This platform was designed as the textbook Kimball use case because that's exactly what it is. FP&A analytics has stable, known business questions, natural dimensions (time, account, cost center, scenario, employee), and a CFO audience who needs answers in seconds — not a complex query planner waiting on 3NF joins.

The engineering philosophy here is deliberate minimalism: solve the real FP&A problem cleanly, normalize sign conventions once instead of trusting every downstream query to get debit/credit logic right, test everything that matters, and add complexity only when it earns its place.

---

_Built for Philippine corporate finance context — GL accounts, cost center codes, subsidiary structures, fiscal calendar, FX rates, and bank names reflect actual corporate group structures in the Philippines._
