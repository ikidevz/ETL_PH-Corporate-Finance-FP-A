import os
import snowflake.connector
from pathlib import Path

PROJECT_ROOT = Path('/opt/airflow')
DATA_DIR = PROJECT_ROOT / 'data'

SNOWFLAKE_WAREHOUSE = 'portfolio_wh'
SNOWFLAKE_DATABASE = 'fpna_db'

COLUMN_MAP = {
    'raw_gl_actuals': [
        'journal_id', 'journal_line', 'entry_type', 'posting_date',
        'fiscal_year', 'fiscal_month', 'period_name', 'gl_account',
        'account_name', 'account_type', 'pnl_line', 'cost_center',
        'subsidiary', 'debit_amount', 'credit_amount', 'net_amount',
        'currency', 'exchange_rate', 'amount_php', 'description',
        'approved_by', 'source_doc',
    ],
    'raw_budget': [
        'fiscal_year', 'fiscal_month', 'period_name', 'gl_account',
        'account_name', 'account_type', 'pnl_line', 'cost_center',
        'subsidiary', 'budget_amount', 'currency', 'scenario',
        'version', 'approved_date', 'approved_by',
    ],
    'raw_forecast': [
        'fiscal_year', 'fiscal_month', 'period_name', 'gl_account',
        'cost_center', 'subsidiary', 'forecast_amount', 'currency',
        'scenario', 'version', 'created_date', 'created_by',
    ],
    'raw_bank_statements': [
        'bank_ref', 'txn_date', 'fiscal_year', 'fiscal_month',
        'bank_account', 'subsidiary', 'bank_name', 'account_type',
        'description', 'reference', 'debit_amount', 'credit_amount',
        'net_amount', 'running_balance', 'currency', 'cf_category',
    ],
    'raw_manual_adjustments': [
        'adjustment_id', 'posting_date', 'fiscal_year', 'fiscal_month',
        'gl_account', 'cost_center', 'subsidiary', 'amount',
        'adjustment_type', 'description', 'supporting_doc',
        'prepared_by', 'approved_by', 'approved_date', 'notes',
    ],
}

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', SNOWFLAKE_WAREHOUSE),
    role=os.getenv('SNOWFLAKE_ROLE'),
    database=os.getenv('SNOWFLAKE_DB', SNOWFLAKE_DATABASE),
    schema='bronze',
)
cur = conn.cursor()

cur.execute("""
    CREATE STAGE IF NOT EXISTS bronze_ingestion
    COMMENT = 'Internal stage for bronze CSV ingestion'
""")

FILES = {
    'raw_gl_actuals':         DATA_DIR / 'erp/raw_gl_actuals.csv',
    'raw_budget':             DATA_DIR / 'budget/raw_annual_budget.csv',
    'raw_forecast':           DATA_DIR / 'budget/raw_revised_forecast.csv',
    'raw_bank_statements':    DATA_DIR / 'banking/raw_bank_statements.csv',
    'raw_manual_adjustments': DATA_DIR / 'excel/raw_manual_adjustments.csv',
}

for table, filepath in FILES.items():
    if not filepath.exists():
        print(f"[WARN] {filepath.name} not found — skipping.")
        continue
    cur.execute(
        f"PUT file://{filepath} @bronze_ingestion OVERWRITE=TRUE AUTO_COMPRESS=TRUE"
    )
    print(f"  ✓ PUT {filepath.name} → @bronze_ingestion")
    cur.execute(f"""
        COPY INTO {SNOWFLAKE_DATABASE}.bronze.{table} ({', '.join(COLUMN_MAP[table])})
        FROM @bronze_ingestion/{filepath.name}.gz
        FILE_FORMAT = (
            TYPE                         = CSV
            SKIP_HEADER                  = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            EMPTY_FIELD_AS_NULL          = TRUE
            NULL_IF                      = ('NULL', 'null', '')
            DATE_FORMAT                  = 'YYYY-MM-DD'
            TIMESTAMP_FORMAT             = 'YYYY-MM-DD HH24:MI:SS'
        )
        ON_ERROR = CONTINUE
    """)
    print(f"  ✓ COPY INTO {table} (with default _source, _loaded_at)")

conn.close()
print("[OK] All bronze tables loaded.")
