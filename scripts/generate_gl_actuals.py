import random
import pandas as pd
from pathlib import Path
from ikidatagen import IkiDataGenerator
from datetime import date, timedelta


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "erp/raw_gl_actuals.csv"


GL_ACCOUNTS = [
    # Revenue
    ('4001', 'Revenue - Retail',
     'Revenue',      'Net Revenue',     'IS', 20),
    ('4002', 'Revenue - Services',
     'Revenue',      'Net Revenue',     'IS', 15),
    ('4003', 'Revenue - Freight',
     'Revenue',      'Net Revenue',     'IS',  8),
    ('4004', 'Revenue - Rental',
     'Revenue',      'Net Revenue',     'IS',  7),
    # COGS
    ('5001', 'Cost of Goods Sold',
     'COGS',         'COGS',            'IS', 18),
    ('5002', 'Direct Labor',                'COGS',
     'COGS',            'IS', 10),
    ('5003', 'Freight & Logistics Cost',
     'COGS',         'COGS',            'IS',  6),
    # OpEx
    ('6001', 'Salaries & Wages',            'OpEx',
     'Personnel Costs', 'IS', 14),
    ('6002', 'Rent & Utilities',            'OpEx',
     'Occupancy',       'IS',  8),
    ('6003', 'Marketing & Advertising',
     'OpEx',         'Marketing',       'IS',  6),
    ('6004', 'Depreciation & Amortization',
     'OpEx',         'D&A',             'IS',  5),
    ('6005', 'Professional Fees',
     'OpEx',         'Admin & General', 'IS',  5),
    ('6006', 'Travel & Entertainment',
     'OpEx',         'Admin & General', 'IS',  4),
    ('6007', 'IT & Communications',
     'OpEx',         'Admin & General', 'IS',  4),
    # Finance & Tax
    ('7001', 'Interest Expense',
     'Finance Cost', 'Finance Costs',   'IS',  5),
    ('7002', 'Bank Charges',
     'Finance Cost', 'Finance Costs',   'IS',  3),
    ('8001', 'Income Tax Expense',
     'Tax',          'Tax',             'IS',  2),
]

GL_WEIGHTS = [a[5] for a in GL_ACCOUNTS]

COST_CENTERS = [
    'CC-RETAIL-MNL', 'CC-RETAIL-CEB', 'CC-RETAIL-DAV',
    'CC-LOGISTICS',  'CC-FINANCE',    'CC-MKTG',
    'CC-HR',         'CC-IT',         'CC-OPS-MNL',
    'CC-SHARED-SVC',
]
SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']
ENTRY_TYPES = ['ACTUAL', 'ACCRUAL', 'REVERSAL', 'RECLASSIFICATION']

MONTHS = 24
ENTRIES_PER_MONTH = 500

rows = []
base = date(2025, 1, 1)

for m in range(MONTHS):
    yr = base.year + (base.month + m - 1) // 12
    mo = (base.month + m - 1) % 12 + 1
    period = date(yr, mo, 1)
    for _ in range(ENTRIES_PER_MONTH):
        schema = [
            {'label': "journal_id", "key_label": "uuid_v4"},
            {"label": "journal_line", "key_label": "number", "options": {
                "min": 1, "max": 10
            }},
            {'label': 'entry_type', 'key_label': 'lambda',
             'options': {'func': lambda: random.choices(ENTRY_TYPES, weights=[75, 15, 5, 5])[0]}},
            {'label': 'posting_date', 'key_label': 'lambda',
             'options': {'func': lambda: (period + timedelta(days=random.randint(0, 27))).isoformat()}},
            {'label': 'fiscal_year', 'key_label': 'lambda',
             'options': {'func': lambda: yr}},
            {'label': 'fiscal_month', 'key_label': 'lambda',
             'options': {'func': lambda: mo}},
            {'label': 'period_name', 'key_label': 'lambda',
             'options': {'func': lambda row: f'{row['fiscal_year']}-{row['fiscal_month']:02d}'}},
            {'label': '_account', 'key_label': 'lambda',
             'options': {'func': lambda: random.choices(GL_ACCOUNTS, weights=GL_WEIGHTS, k=1)[0]}},
            {'label': 'gl_account', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_account'][0]}},
            {'label': 'account_name', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_account'][1]}},
            {'label': 'account_type', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_account'][2]}},
            {'label': 'pnl_line', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_account'][3]}},
            {'label': 'cost_center', 'key_label': 'custom_list',
             'options': {'values': COST_CENTERS}},
            {'label': 'subsidiary', 'key_label': 'custom_list',
             'options': {'values': SUBSIDIARIES}},
            {'label': '_is_expense', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_account'][2] in ['COGS', 'OpEx', 'Finance Cost', 'Tax']}},
            {"label": "_amount", "key_label": "number", "options": {
                "min": 5000, "max": 5000000, "decimals": 2
            }},
            {'label': 'debit_amount', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_amount'] if row['_is_expense'] else 0}},
            {'label': 'credit_amount', 'key_label': 'lambda',
             'options': {'func': lambda row: 0 if row['_is_expense'] else row['_amount']}},
            {'label': 'net_amount', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_amount'] if row['_is_expense'] else -row['_amount']}},
            {'label': 'currency', 'key_label': 'lambda',
             'options': {'func': lambda: 'PHP'}},
            {'label': 'exchange_rate', 'key_label': 'lambda',
             'options': {'func': lambda: 1.0}},
            {'label': 'amount_php', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_amount']}},
            {'label': 'description', 'key_label': 'catch_praise'},
            {'label': 'approved_by', 'key_label': 'full_name'},
            {'label': 'source_doc', 'key_label': 'character_sequence',
             'options': {'pattern': "DOC-%%%%-########"}},
        ]

        rows.append(IkiDataGenerator(schema).one())

df = pd.DataFrame(rows)
df = df.drop(columns=['_account', '_is_expense', '_amount'])
df.to_csv(output_path, index=False)
print(f"Generated {len(df):,} GL actual rows → data/erp/raw_gl_actuals.csv")
