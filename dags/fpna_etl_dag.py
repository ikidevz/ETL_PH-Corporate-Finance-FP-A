import os
import subprocess
from datetime import datetime
from pathlib import Path

from airflow.sdk import DAG, task

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path('/opt/airflow')
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
DBT_PROJECT_DIR = PROJECT_ROOT / 'dbt'
DBT_PROFILES_DIR = PROJECT_ROOT / 'dbt'
DBT_PROFILE = 'fpna'

# ---------------------------------------------------------------------------
# Snowflake constants
# ---------------------------------------------------------------------------
SNOWFLAKE_WAREHOUSE = 'portfolio_wh'
SNOWFLAKE_DATABASE = 'fpna_db'

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
DEFAULT_ARGS = {
    'owner': 'ikidevs',
    'depends_on_past': False,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dbt(*args: str) -> None:
    """Run a dbt command inside DBT_PROJECT_DIR. Raises on non-zero exit."""
    subprocess.run(
        [
            'dbt', *args,
            '--profiles-dir', str(DBT_PROFILES_DIR),
            '--profile',      DBT_PROFILE,
        ],
        cwd=str(DBT_PROJECT_DIR),
        check=True,
    )


with DAG(
    dag_id='ph_corporate_fpna_pipeline',
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=['fpna', 'finance', 'corporate'],
) as dag:

    # -----------------------------------------------------------------------
    # Stage 1 — Generate source CSVs (all run in parallel)
    # -----------------------------------------------------------------------

    @task
    def generate_gl_actuals():
        """Generate raw_gl_actuals.csv — 24 months of GL journal entries."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_gl_actuals.py')], check=True)
        print('[OK] GL actuals generated.')

    @task
    def generate_budget():
        """Generate raw_annual_budget.csv — FY2024 + FY2025 annual budget."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_budget.py')], check=True)
        print('[OK] Budget generated.')

    @task
    def generate_forecast():
        """Generate raw_revised_forecast.csv — RF1/RF2/RF3 rolling forecasts."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_forecast.py')], check=True)
        print('[OK] Forecast generated.')

    @task
    def generate_bank_statements():
        """Generate raw_bank_statements.csv — 18 months of bank feeds."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_bank_statements.py')], check=True)
        print('[OK] Bank statements generated.')

    @task
    def generate_manual_adjustments():
        """Generate raw_manual_adjustments.csv — month-end Excel adjustments."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_manual_adjustments.py')], check=True)
        print('[OK] Manual adjustments generated.')

    @task
    def generate_chart_of_accounts():
        """Generate chart_of_accounts.csv — GL account to P&L line mapping seed."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_chart_of_accounts.py')], check=True)
        print('[OK] Chart of accounts generated.')

    @task
    def generate_cost_center_hierarchy():
        """Generate cost_center_hierarchy.csv — cost center to subsidiary mapping seed."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_cost_center_hierarchy.py')], check=True)
        print('[OK] Cost center hierarchy generated.')

    @task
    def generate_ph_fiscal_calendar():
        """Generate ph_fiscal_calendar.csv — PH fiscal year definition seed."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_ph_fiscal_calendar.py')], check=True)
        print('[OK] PH fiscal calendar generated.')

    @task
    def generate_fx_rates():
        """Generate fx_rates.csv — USD/PHP monthly FX rates seed."""
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'generate_fx_rates.py')], check=True)
        print('[OK] FX rates generated.')

    # -----------------------------------------------------------------------
    # Stage 2 — Snowflake setup + bronze load
    # -----------------------------------------------------------------------

    @task
    def load_init_snowflake():
        """
        CREATE OR REPLACE bronze tables + control schema.
        Safe to re-run — idempotent DDL.
        """
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'load_init_snowflake.py')], check=True)
        print('[OK] Snowflake setup completed.')

    @task
    def load_bronze():
        """
        PUT + COPY INTO all five bronze tables.
        PUT uses OVERWRITE=TRUE; COPY INTO skips already-loaded file hashes.
        """
        subprocess.run(
            ['python', str(SCRIPTS_DIR / 'load_bronze.py')], check=True)
        print('[OK] Data loaded into Snowflake bronze.')

    # -----------------------------------------------------------------------
    # Stage 3 — dbt: deps → seeds → staging → core → reporting → tests
    # -----------------------------------------------------------------------

    @task
    def dbt_deps():
        """Install dbt_utils + dbt_expectations packages. Safe to re-run."""
        _dbt('deps')
        print('[OK] dbt dependencies installed.')

    @task
    def dbt_seed():
        """
        Load chart_of_accounts, cost_center_hierarchy, ph_fiscal_calendar,
        fx_rates into gold schema. --full-refresh keeps seeds in sync on every run.
        """
        _dbt('seed', '--full-refresh')
        print('[OK] dbt seeds loaded.')

    @task
    def dbt_run_staging():
        """
        Recreate staging views over fresh bronze data:
        stg_gl_actuals, stg_budget, stg_forecast, stg_bank_statements,
        stg_manual_adjustments. Views are always idempotent.
        """
        _dbt('run', '--select', 'staging')
        print('[OK] dbt staging models complete.')

    @task
    def dbt_run_core():
        """
        Build dims (table) + facts (incremental) in marts.core.
        dbt resolves internal order via the ref() DAG.
        Models: dim_date, dim_account, dim_cost_center, dim_subsidiary,
                dim_scenario, fct_gl_actuals, fct_budget, fct_forecast, fct_cash_flow.
        """
        _dbt('run', '--select', 'marts.core')
        print('[OK] dbt core models complete.')

    @task
    def dbt_run_reporting():
        """
        Build marts.reporting models:
          - rpt_variance_analysis    Actual vs Budget vs Forecast by account × CC
          - rpt_pnl_summary          Revenue → Gross Profit → EBITDA → Net Income
          - rpt_cash_flow_statement  Operating / Investing / Financing CF
          - rpt_executive_dashboard  CFO-level KPI rollup
        """
        _dbt('run', '--select', 'marts.reporting')
        print('[OK] dbt reporting models complete.')

    @task
    def dbt_test():
        """
        Run all dbt schema tests (not_null, unique, accepted_values,
        dbt_expectations) + singular test assert_budget_equals_actuals_period.
        Fails the DAG on any data quality violation.
        """
        _dbt('test')
        print('[OK] dbt tests passed.')

    t_gl = generate_gl_actuals()
    t_budget = generate_budget()
    t_fc = generate_forecast()
    t_bank = generate_bank_statements()
    t_adj = generate_manual_adjustments()
    t_coa = generate_chart_of_accounts()
    t_cc = generate_cost_center_hierarchy()
    t_cal = generate_ph_fiscal_calendar()
    t_fx = generate_fx_rates()
    t_init = load_init_snowflake()
    t_bronze = load_bronze()
    t_deps = dbt_deps()
    t_seed = dbt_seed()
    t_staging = dbt_run_staging()
    t_core = dbt_run_core()
    t_rpt = dbt_run_reporting()
    t_tests = dbt_test()

    [t_gl, t_budget, t_fc, t_bank, t_adj] >> t_init >> t_bronze >> t_deps
    [t_coa, t_cc, t_cal, t_fx] >> t_deps
    t_deps >> t_seed >> t_staging >> t_core >> t_rpt >> t_tests
