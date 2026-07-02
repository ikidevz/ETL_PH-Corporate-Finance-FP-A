import os
import snowflake.connector

SNOWFLAKE_WAREHOUSE = 'portfolio_wh'
SNOWFLAKE_DATABASE = 'fpna_db'
SNOWFLAKE_SCHEMAS = ['bronze', 'silver', 'gold', 'control']

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
)
cur = conn.cursor()

# ── Warehouse ─────────────────────────────────────────────────────────
cur.execute(f"""
    CREATE WAREHOUSE IF NOT EXISTS {SNOWFLAKE_WAREHOUSE}
        WAREHOUSE_SIZE = 'X-SMALL'
        AUTO_SUSPEND   = 60
        AUTO_RESUME    = TRUE
        COMMENT        = 'Shared warehouse for all portfolio projects'
""")
print(f"[OK] Warehouse {SNOWFLAKE_WAREHOUSE} ensured.")

# ── Database ──────────────────────────────────────────────────────────
cur.execute(f"CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DATABASE}")
cur.execute(f"USE DATABASE {SNOWFLAKE_DATABASE}")
print(f"[OK] Database {SNOWFLAKE_DATABASE} ensured.")

# ── Schemas ───────────────────────────────────────────────────────────
for schema in SNOWFLAKE_SCHEMAS:
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_DATABASE}.{schema}")
    print(f"[OK] Schema {SNOWFLAKE_DATABASE}.{schema} ensured.")

# ── Bronze tables (CREATE OR REPLACE = always idempotent) ─────────────
bronze_tables = {
    "raw_gl_actuals": """
        journal_id      VARCHAR,
        journal_line    INTEGER,
        entry_type      VARCHAR,
        posting_date    DATE,
        fiscal_year     INTEGER,
        fiscal_month    INTEGER,
        period_name     VARCHAR,
        gl_account      VARCHAR,
        account_name    VARCHAR,
        account_type    VARCHAR,
        pnl_line        VARCHAR,
        cost_center     VARCHAR,
        subsidiary      VARCHAR,
        debit_amount    NUMERIC(18,2),
        credit_amount   NUMERIC(18,2),
        net_amount      NUMERIC(18,2),
        currency        VARCHAR,
        exchange_rate   NUMERIC(10,6),
        amount_php      NUMERIC(18,2),
        description     VARCHAR,
        approved_by     VARCHAR,
        source_doc      VARCHAR,
        _source         VARCHAR   DEFAULT 'ERP',
        _loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_budget": """
        fiscal_year     INTEGER,
        fiscal_month    INTEGER,
        period_name     VARCHAR,
        gl_account      VARCHAR,
        account_name    VARCHAR,
        account_type    VARCHAR,
        pnl_line        VARCHAR,
        cost_center     VARCHAR,
        subsidiary      VARCHAR,
        budget_amount   NUMERIC(18,2),
        currency        VARCHAR,
        scenario        VARCHAR,
        version         VARCHAR,
        approved_date   DATE,
        approved_by     VARCHAR,
        _source         VARCHAR   DEFAULT 'BUDGET_UPLOAD',
        _loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_forecast": """
        fiscal_year      INTEGER,
        fiscal_month     INTEGER,
        period_name      VARCHAR,
        gl_account       VARCHAR,
        cost_center      VARCHAR,
        subsidiary       VARCHAR,
        forecast_amount  NUMERIC(18,2),
        currency         VARCHAR,
        scenario         VARCHAR,
        version          VARCHAR,
        created_date     DATE,
        created_by       VARCHAR,
        _source          VARCHAR   DEFAULT 'FORECAST_UPLOAD',
        _loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_bank_statements": """
        bank_ref         VARCHAR,
        txn_date         DATE,
        fiscal_year      INTEGER,
        fiscal_month     INTEGER,
        bank_account     VARCHAR,
        subsidiary       VARCHAR,
        bank_name        VARCHAR,
        account_type     VARCHAR,
        description      VARCHAR,
        reference        VARCHAR,
        debit_amount     NUMERIC(18,2),
        credit_amount    NUMERIC(18,2),
        net_amount       NUMERIC(18,2),
        running_balance  NUMERIC(18,2),
        currency         VARCHAR   DEFAULT 'PHP',
        cf_category      VARCHAR,
        _source          VARCHAR   DEFAULT 'BANK_FEED',
        _loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_manual_adjustments": """
        adjustment_id    VARCHAR,
        posting_date     DATE,
        fiscal_year      INTEGER,
        fiscal_month     INTEGER,
        gl_account       VARCHAR,
        cost_center      VARCHAR,
        subsidiary       VARCHAR,
        amount           NUMERIC(18,2),
        adjustment_type  VARCHAR,
        description      VARCHAR,
        supporting_doc   VARCHAR,
        prepared_by      VARCHAR,
        approved_by      VARCHAR,
        approved_date    DATE,
        notes            VARCHAR,
        _source          VARCHAR   DEFAULT 'EXCEL_UPLOAD',
        _loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_employee_roster": """
        employee_id        VARCHAR,
        full_name          VARCHAR,
        cost_center        VARCHAR,
        subsidiary         VARCHAR,
        job_level          VARCHAR,
        monthly_base_php   NUMERIC(18,2),
        hire_date          DATE,
        termination_date   DATE,
        employment_status  VARCHAR,
        _source            VARCHAR   DEFAULT 'HRIS',
        _loaded_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_ap_ar": """
        invoice_id       VARCHAR,
        doc_type         VARCHAR,
        invoice_date     DATE,
        due_date         DATE,
        fiscal_year      INTEGER,
        fiscal_month     INTEGER,
        subsidiary       VARCHAR,
        counterparty     VARCHAR,
        amount_php       NUMERIC(18,2),
        status           VARCHAR,
        paid_date        DATE,
        _source          VARCHAR   DEFAULT 'ERP',
        _loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",

    "raw_intercompany": """
        intercompany_id  VARCHAR,
        posting_date     DATE,
        fiscal_year      INTEGER,
        fiscal_month     INTEGER,
        from_subsidiary  VARCHAR,
        to_subsidiary    VARCHAR,
        ic_type          VARCHAR,
        amount_php       NUMERIC(18,2),
        description      VARCHAR,
        _source          VARCHAR   DEFAULT 'ERP',
        _loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()""",
}

for table, columns in bronze_tables.items():
    cur.execute(
        f"CREATE OR REPLACE TABLE {SNOWFLAKE_DATABASE}.bronze.{table} ({columns})")
    print(f"[OK] Table {SNOWFLAKE_DATABASE}.bronze.{table} ensured.")

# ── Control table (IF NOT EXISTS — preserves existing close flags) ─────
cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {SNOWFLAKE_DATABASE}.control.period_lock (
        fiscal_year   INTEGER,
        fiscal_month  INTEGER,
        period_status VARCHAR DEFAULT 'OPEN',
        closed_date   DATE,
        closed_by     VARCHAR
    )
""")
print(f"[OK] Table {SNOWFLAKE_DATABASE}.control.period_lock ensured.")

# Seed all periods as OPEN on first run (MERGE is idempotent).
# Year range must stay in sync with generate_ph_fiscal_calendar.py.
FISCAL_YEARS_LOCK = [2023, 2024, 2025]   # <-- update when data window expands
year_union = '\n            UNION ALL '.join(
    [f'SELECT {y} AS fy' for y in FISCAL_YEARS_LOCK]
)
cur.execute(f"""
MERGE INTO {SNOWFLAKE_DATABASE}.control.period_lock AS t
USING (
    SELECT
        y.fy AS fiscal_year,
        m.fm AS fiscal_month
    FROM (
        {year_union}
    ) y
    CROSS JOIN (
        SELECT 1 AS fm
        UNION ALL SELECT 2
        UNION ALL SELECT 3
        UNION ALL SELECT 4
        UNION ALL SELECT 5
        UNION ALL SELECT 6
        UNION ALL SELECT 7
        UNION ALL SELECT 8
        UNION ALL SELECT 9
        UNION ALL SELECT 10
        UNION ALL SELECT 11
        UNION ALL SELECT 12
    ) m
) s
ON t.fiscal_year = s.fiscal_year
AND t.fiscal_month = s.fiscal_month
WHEN NOT MATCHED THEN
    INSERT (
        fiscal_year,
        fiscal_month,
        period_status
    )
    VALUES (
        s.fiscal_year,
        s.fiscal_month,
        'OPEN'
    );
""")
print("[OK] control.period_lock seeded (OPEN for all periods).")

conn.close()
print("[OK] Snowflake schemas + bronze tables initialised (idempotent).")
