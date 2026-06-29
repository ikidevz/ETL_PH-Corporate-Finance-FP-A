import random
import pandas as pd
from pathlib import Path
from ikidatagen import IkiDataGenerator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "budget/raw_annual_budget.csv"

GL_ACCOUNTS = [
    ('4001', 'Revenue - Retail',            'Revenue',      'Net Revenue'),
    ('4002', 'Revenue - Services',          'Revenue',      'Net Revenue'),
    ('4003', 'Revenue - Freight',           'Revenue',      'Net Revenue'),
    ('4004', 'Revenue - Rental',            'Revenue',      'Net Revenue'),
    ('5001', 'Cost of Goods Sold',          'COGS',         'COGS'),
    ('5002', 'Direct Labor',                'COGS',         'COGS'),
    ('5003', 'Freight & Logistics Cost',    'COGS',         'COGS'),
    ('6001', 'Salaries & Wages',            'OpEx',         'Personnel Costs'),
    ('6002', 'Rent & Utilities',            'OpEx',         'Occupancy'),
    ('6003', 'Marketing & Advertising',     'OpEx',         'Marketing'),
    ('6004', 'Depreciation & Amortization', 'OpEx',         'D&A'),
    ('6005', 'Professional Fees',           'OpEx',         'Admin & General'),
    ('6006', 'Travel & Entertainment',      'OpEx',         'Admin & General'),
    ('6007', 'IT & Communications',         'OpEx',         'Admin & General'),
    ('7001', 'Interest Expense',            'Finance Cost', 'Finance Costs'),
    ('7002', 'Bank Charges',                'Finance Cost', 'Finance Costs'),
    ('8001', 'Income Tax Expense',          'Tax',          'Tax'),
]
COST_CENTERS = ['CC-RETAIL-MNL', 'CC-RETAIL-CEB', 'CC-RETAIL-DAV',
                'CC-LOGISTICS', 'CC-FINANCE', 'CC-MKTG', 'CC-HR',
                'CC-IT', 'CC-OPS-MNL', 'CC-SHARED-SVC']
SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']
FISCAL_YEARS = [2025, 2026]

rows = []

for fy in FISCAL_YEARS:
    for mo in range(1, 13):
        for acct in GL_ACCOUNTS:
            for cc in COST_CENTERS:
                for sub in SUBSIDIARIES:
                    seasonality = 1.3 if (mo == 12 and acct[2] == 'Revenue') \
                        else 1.1 if mo in [11, 3, 4] else 1.0
                    schema = [
                        {'label': 'fiscal_year', 'key_label': 'lambda',
                         'options': {'func': lambda: fy}},
                        {'label': 'fiscal_month', 'key_label': 'lambda',
                         'options': {'func': lambda: mo}},
                        {'label': 'period_name', 'key_label': 'lambda',
                         'options': {'func': lambda row: f'{row['fiscal_year']}-{row['fiscal_month']:02d}'}},
                        {'label': 'gl_account', 'key_label': 'lambda',
                         'options': {'func': lambda: acct[0]}},
                        {'label': 'account_name', 'key_label': 'lambda',
                         'options': {'func': lambda: acct[1]}},
                        {'label': 'account_type', 'key_label': 'lambda',
                         'options': {'func': lambda: acct[2]}},
                        {'label': 'pnl_line', 'key_label': 'lambda',
                         'options': {'func': lambda: acct[3]}},
                        {'label': 'cost_center', 'key_label': 'lambda',
                         'options': {'func': lambda: cc}},
                        {'label': 'subsidiary', 'key_label': 'lambda',
                         'options': {'func': lambda: sub}},
                        {'label': 'budget_amount', 'key_label': 'lambda',
                         'options': {'func': lambda: round(random.uniform(50_000, 3_000_000) * seasonality, 2)}},
                        {'label': 'currency', 'key_label': 'lambda',
                         'options': {'func': lambda: 'PHP'}},
                        {'label': 'scenario', 'key_label': 'lambda',
                         'options': {'func': lambda: 'ANNUAL_BUDGET'}},
                        {'label': 'version', 'key_label': 'lambda',
                         'options': {'func': lambda: 'v1.0'}},
                        {'label': 'approved_date', 'key_label': 'lambda',
                         'options': {'func': lambda row: f'{row['fiscal_year'] - 1}-11-30'}},
                        {'label': 'approved_by', 'key_label': 'lambda',
                         'options': {'func': lambda: 'CFO'}},
                    ]

                    rows.append(IkiDataGenerator(schema).one())


df = pd.DataFrame(rows)
df.to_csv(output_path, index=False)
print(f"Generated {len(df):,} budget rows → data/budget/raw_annual_budget.csv")
