import random
import pandas as pd
from pathlib import Path
from ikidatagen import IkiDataGenerator
from datetime import date, datetime, timedelta


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "excel/raw_manual_adjustments.csv"

GL_ACCOUNTS = [
    '4001', '4002', '4003', '4004',         # Revenue
    '5001', '5002', '5003',                 # COGS
    '6001', '6002', '6003', '6004', '6005',  # OpEx
    '6006', '6007',                         # OpEx (Admin)
    '7001', '7002',                         # Finance Cost
    '8001',                                 # Tax
]
COST_CENTERS = ['CC-RETAIL-MNL', 'CC-LOGISTICS',
                'CC-FINANCE', 'CC-MKTG', 'CC-HR']
SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']
ADJ_TYPES = ['ACCRUAL', 'REVERSAL', 'RECLASSIFICATION', 'CORRECTION']
APPROVERS = ['CFO', 'Controller', 'Finance Manager', 'VP Finance']

MONTHS = 24
PER_MONTH = 30

rows = []
base = date(2025, 1, 1)

for m in range(MONTHS):
    yr = base.year + (base.month + m - 1) // 12
    mo = (base.month + m - 1) % 12 + 1
    for _ in range(PER_MONTH):
        close_day = date(yr, mo, 28)
        adj_type = random.choices(ADJ_TYPES, weights=[40, 30, 20, 10])[0]
        schema = [
            {'label': "adjustment_id", "key_label": "uuid_v4"},
            {'label': 'posting_date', 'key_label': 'lambda',
             'options': {'func': lambda: (close_day - timedelta(days=random.randint(0, 3))).isoformat()}},
            {'label': 'fiscal_year', 'key_label': 'lambda',
             'options': {'func': lambda: yr}},
            {'label': 'fiscal_month', 'key_label': 'lambda',
             'options': {'func': lambda: mo}},
            {'label': 'gl_account', 'key_label': 'custom_list',
             'options': {'values': GL_ACCOUNTS}},
            {'label': 'cost_center', 'key_label': 'custom_list',
             'options': {'values': COST_CENTERS}},
            {'label': 'subsidiary', 'key_label': 'custom_list',
             'options': {'values': SUBSIDIARIES}},
            {'label': '_amount', 'key_label': 'number',
             'options': {'min': 1000, 'max': 5000000, "decimals": 2}},
            {'label': '_adj_type', 'key_label': 'lambda',
             'options': {'func': lambda: random.choices(ADJ_TYPES, weights=[40, 30, 20, 10])[0]}},
            {'label': 'amount', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_amount'] if adj_type != 'REVERSAL' else -row['_amount']}},
            {'label': 'adjustment_type', 'key_label': 'lambda',
             'options': {'func': lambda row: row['_adj_type']}},
            {'label': 'description', 'key_label': 'catch_praise'},
            {'label': 'supporting_doc', 'key_label': 'character_sequence',
             'options': {'pattern': "ADJ-%%%-#######.xlsx"}},
            {'label': 'prepared_by', 'key_label': 'full_name'},
            {'label': 'approved_by', 'key_label': 'custom_list',
             'options': {'values': APPROVERS}},
            {'label': 'approved_date', 'key_label': 'lambda',
             'options': {'func': lambda row:  (datetime.fromisoformat(row['posting_date']) + timedelta(days=1)).strftime("%Y-%m-%d")}},
            {'label': 'notes', 'key_label': 'lambda',
             'options': {'func': lambda row:  row['gl_account'] + ' ' + row['cost_center'] + ' ' + row['subsidiary']}},
        ]

        rows.append(IkiDataGenerator(schema).one())

df = pd.DataFrame(rows)
df = df.drop(columns=['_amount', '_adj_type'])
df.to_csv(output_path, index=False)
print(
    f"Generated {len(df):,} manual adjustment rows → data/excel/raw_manual_adjustments.csv")
