import random
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from ikidatagen import IkiDataGenerator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "intercompany/raw_intercompany.csv"

SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']
IC_TYPES = ['SHARED_SERVICE_CHARGE', 'INTERCOMPANY_LOAN', 'MGMT_FEE']

MONTHS = 24
rows = []
base = date(2023, 1, 1)

for m in range(MONTHS):
    yr = base.year + (base.month + m - 1) // 12
    mo = (base.month + m - 1) % 12 + 1
    period = date(yr, mo, 1)
    for _ in range(random.randint(5, 15)):
        from_sub, to_sub = random.sample(SUBSIDIARIES, 2)
        schema = [
            {'label': 'intercompany_id', 'key_label': 'uuid_v4'},
            {'label': 'posting_date', 'key_label': 'lambda',
             'options': {'func': lambda:  (period + timedelta(days=random.randint(0, 27))).isoformat()}},
            {'label': 'fiscal_year', 'key_label': 'lambda',
             'options': {'func': lambda:  yr}},
            {'label': 'fiscal_month', 'key_label': 'lambda',
             'options': {'func': lambda:  mo}},
            {'label': 'from_subsidiary', 'key_label': 'lambda',
             'options': {'func': lambda:  from_sub}},
            {'label': 'to_subsidiary', 'key_label': 'lambda',
             'options': {'func': lambda:  to_sub}},
            {'label': 'ic_type', 'key_label': 'custom_list',
             'options': {'values': SUBSIDIARIES}},
            {"label": "amount_php", "key_label": "number", "options": {
                "min": 50000, "max": 2000000, "decimals": 2
            }},
            {'label': 'description', 'key_label': 'catch_praise'},
        ]
        payload = IkiDataGenerator(schema).one()
        rows.append(payload)

df = pd.DataFrame(rows)
df.to_csv(output_path, index=False)
print(f'Generated {len(df)} cross sussidiary postings → {output_path}')
