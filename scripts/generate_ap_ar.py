import uuid
import random
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta
from ikidatagen import IkiDataGenerator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "ap_ar/raw_ap_ar.csv"

SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']
DOC_TYPES = ['AP', 'AR']
STATUSES = ['OPEN', 'PAID', 'OVERDUE']

MONTHS = 24
rows = []
base = date(2025, 1, 1)

for m in range(MONTHS):
    yr = base.year + (base.month + m - 1) // 12
    mo = (base.month + m - 1) % 12 + 1
    period = date(yr, mo, 1)

    for _ in range(random.randint(20, 60)):
        schema = [
            {'label': '_doc_type', 'key_label': 'custom_list',
             'options': {'values': DOC_TYPES}},
            {'label': 'invoice_id', 'key_label': 'lambda',
             'options': {'func': lambda row:  f'{row['_doc_type']}-{str(uuid.uuid4())[:8].upper()}'}},
            {'label': 'doc_type', 'key_label': 'lambda',
             'options': {'func': lambda row:  row['_doc_type']}},
            {'label': 'invoice_date', 'key_label': 'lambda',
             'options': {'func': lambda:  (period + timedelta(days=random.randint(0, 27))).isoformat()}},
            {'label': 'due_date', 'key_label': 'lambda',
             'options': {'func': lambda row: (datetime.fromisoformat(row['invoice_date']) + timedelta(days=random.choice([15, 30, 45, 60]))).isoformat()}},
            {'label': 'fiscal_year', 'key_label': 'lambda',
             'options': {'func': lambda:  yr}},
            {'label': 'fiscal_month', 'key_label': 'lambda',
             'options': {'func': lambda:  mo}},
            {'label': 'subsidiary', 'key_label': 'custom_list',
             'options': {'values': SUBSIDIARIES}},
            {'label': 'counterparty', 'key_label': 'company_name'},
            {"label": "amount_php", "key_label": "number", "options": {
                "min": 10000, "max": 3000000, "decimals": 2
            }},
            {'label': 'status', 'key_label': 'lambda',
             'options': {'func': lambda:  random.choices(STATUSES, weights=[30, 60, 10])[0]}},
            {'label': 'paid_date', 'key_label': 'lambda',
             'options': {'func': lambda row: (datetime.fromisoformat(row['due_date']) + timedelta(days=random.randint(-10, 5))).isoformat() if row['status'] == 'PAID' else None}},
        ]
        payload = IkiDataGenerator(schema).one()
        rows.append(payload)

df = pd.DataFrame(rows)
df = df.drop(columns=['_doc_type'])
df.to_csv(output_path, index=False)
print(f'Generated {len(df)} accounts payable → {output_path}')
