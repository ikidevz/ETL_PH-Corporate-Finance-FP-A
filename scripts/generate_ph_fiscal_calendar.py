import pandas as pd
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path("dbt/seeds")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fx_path = OUTPUT_DIR / "ph_fiscal_calendar.csv"

ACTUALS_START_YEAR = 2025   # base year in generate_gl_actuals.py
ACTUALS_MONTHS = 24     # MONTHS constant in generate_gl_actuals.py
BUDGET_YEARS = [2025, 2026]   # FISCAL_YEARS in generate_budget.py

_actuals_end_year = date(
    ACTUALS_START_YEAR + (ACTUALS_MONTHS - 1) // 12,
    (ACTUALS_MONTHS - 1) % 12 + 1,
    1
).year

FISCAL_YEARS = sorted(set(
    list(range(ACTUALS_START_YEAR, _actuals_end_year + 1)) + BUDGET_YEARS
))

rows = []

for fy in FISCAL_YEARS:
    for mo in range(1, 13):
        if mo <= 3:
            quarter = 1
        elif mo <= 6:
            quarter = 2
        elif mo <= 9:
            quarter = 3
        else:
            quarter = 4

        rows.append({
            'fiscal_year':    fy,
            'fiscal_month':   mo,
            'calendar_year':  fy,
            'calendar_month': mo,
            'fiscal_quarter': quarter,
            'period_name':    f'{fy}-{mo:02d}',
            'quarter_name':   f'{fy}-Q{quarter}',
            'is_q4':          quarter == 4,
            'is_year_end':    mo == 12,
        })

df = pd.DataFrame(rows)
df.to_csv(fx_path, index=False)
print(f"Generated {len(df)} periods → dbt/seeds/ph_fiscal_calendar.csv")
