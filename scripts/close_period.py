import os
import sys
import snowflake.connector

SNOWFLAKE_DATABASE = 'fpna_db'

fiscal_year = int(sys.argv[1])
fiscal_month = int(sys.argv[2])
closed_by = sys.argv[3] if len(sys.argv) > 3 else 'FP&A Team'

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'portfolio_wh'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    database=SNOWFLAKE_DATABASE,
)
cur = conn.cursor()

cur.execute(f"""
    MERGE INTO {SNOWFLAKE_DATABASE}.control.period_lock AS t
    USING (SELECT {fiscal_year} AS fy, {fiscal_month} AS fm) AS s
    ON t.fiscal_year = s.fy AND t.fiscal_month = s.fm
    WHEN MATCHED THEN UPDATE SET
        period_status = 'CLOSED',
        closed_date   = CURRENT_DATE(),
        closed_by     = '{closed_by}'
    WHEN NOT MATCHED THEN INSERT
        (fiscal_year, fiscal_month, period_status, closed_date, closed_by)
        VALUES ({fiscal_year}, {fiscal_month}, 'CLOSED', CURRENT_DATE(), '{closed_by}')
""")

conn.close()
print(f"[OK] Closed {fiscal_year}-{fiscal_month:02d} (by: {closed_by})")
