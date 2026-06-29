import random
import pandas as pd
from pathlib import Path
from ikidatagen import IkiDataGenerator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "budget/raw_revised_forecast.csv"

GL_ACCOUNTS = [
    '4001', '4002', '4003', '4004',
    '5001', '5002', '5003',
    '6001', '6002', '6003', '6004', '6005',
    '6006', '6007',
    '7001', '7002',
    '8001',
]
COST_CENTERS = ['CC-RETAIL-MNL', 'CC-RETAIL-CEB', 'CC-RETAIL-DAV',
                'CC-LOGISTICS', 'CC-FINANCE', 'CC-MKTG', 'CC-HR',
                'CC-IT', 'CC-OPS-MNL', 'CC-SHARED-SVC']
SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']

VERSIONS = [('RF1', '2025-04-15'), ('RF2', '2025-07-15'),
            ('RF3', '2025-10-15')]
FISCAL_YEAR = 2025

rows = []

for version, created_date in VERSIONS:
    for mo in range(1, 13):
        for acct in GL_ACCOUNTS:
            for cc in COST_CENTERS:
                for sub in SUBSIDIARIES:
                    schema = [
                        {'label': 'fiscal_year', 'key_label': 'lambda',
                         'options': {'func': lambda: FISCAL_YEAR}},
                        {'label': 'fiscal_month', 'key_label': 'lambda',
                         'options': {'func': lambda: mo}},
                        {'label': 'period_name', 'key_label': 'lambda',
                         'options': {'func': lambda row: f'{row['fiscal_year']}-{row['fiscal_month']:02d}'}},
                        {'label': 'gl_account', 'key_label': 'lambda',
                         'options': {'func': lambda: acct}},
                        {'label': 'cost_center', 'key_label': 'lambda',
                         'options': {'func': lambda: cc}},
                        {'label': 'subsidiary', 'key_label': 'lambda',
                         'options': {'func': lambda: sub}},
                        {'label': 'forecast_amount', 'key_label': 'lambda',
                         'options': {'func': lambda: round(random.uniform(50_000, 3_000_000) * random.uniform(0.85, 1.15), 2)}},
                        {'label': 'currency', 'key_label': 'lambda',
                         'options': {'func': lambda: 'PHP'}},
                        {'label': 'scenario', 'key_label': 'lambda',
                         'options': {'func': lambda: 'REVISED_FORECAST'}},
                        {'label': 'version', 'key_label': 'lambda',
                         'options': {'func': lambda: version}},
                        {'label': 'created_date', 'key_label': 'lambda',
                         'options': {'func': lambda: created_date}},
                        {'label': 'created_by', 'key_label': 'lambda',
                         'options': {'func': lambda: 'FP&A Team'}},
                    ]

                    rows.append(IkiDataGenerator(schema).one())

df = pd.DataFrame(rows)
df.to_csv(output_path, index=False)
print(
    f"Generated {len(df):,} forecast rows → data/budget/raw_revised_forecast.csv")
