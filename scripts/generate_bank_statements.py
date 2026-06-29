import random
import pandas as pd
from pathlib import Path
from ikidatagen import IkiDataGenerator
from datetime import date


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "banking/raw_bank_statements.csv"

BANK_ACCOUNTS = [
    {'acct': 'BDO-SUB-A-OPS',  'sub': 'SUB_A',
        'type': 'OPERATING',   'bank': 'BDO'},
    {'acct': 'BPI-SUB-B-OPS',  'sub': 'SUB_B',
        'type': 'OPERATING',   'bank': 'BPI'},
    {'acct': 'MBT-SUB-C-OPS',  'sub': 'SUB_C',
        'type': 'OPERATING',   'bank': 'Metrobank'},
    {'acct': 'BDO-SUB-D-PAY',  'sub': 'SUB_D',
        'type': 'PAYROLL',     'bank': 'BDO'},
    {'acct': 'BPI-SUB-E-OPS',  'sub': 'SUB_E',
        'type': 'OPERATING',   'bank': 'BPI'},
    {'acct': 'LBP-GROUP-TAX',  'sub': 'GROUP',
        'type': 'TAX_PAYMENT', 'bank': 'LandBank'},
]
TXN_DESCS = {
    'OPERATING':   ['Customer Payment', 'Sales Collection', 'Vendor Payment',
                    'Utility Payment', 'Rent Payment', 'Service Revenue'],
    'PAYROLL':     ['Payroll Release', 'SSS Contribution', 'PhilHealth',
                    'Pag-IBIG', '13th Month Pay', 'Bonus Release'],
    'TAX_PAYMENT': ['VAT Remittance', 'Income Tax', 'Withholding Tax',
                    'CWT Payment', 'Excise Tax'],
}

MONTHS = 18
rows = []
start = date(2025, 1, 1)

for m in range(MONTHS):
    yr = start.year + (start.month + m - 1) // 12
    mo = (start.month + m - 1) % 12 + 1
    for ba in BANK_ACCOUNTS:
        running_bal = round(random.uniform(500_000, 50_000_000), 2)
        for _ in range(random.randint(30, 150)):
            schema = [
                {'label': "_bank_ref", "key_label": "uuid_v4"},
                {'label': 'bank_ref', 'key_label': 'lambda',
                 'options': {'func': lambda row: row['_bank_ref'][:12].upper()}},
                {'label': 'txn_date', 'key_label': 'lambda',
                 'options': {'func': lambda: date(yr, mo, random.randint(1, 28)).isoformat()}},
                {'label': 'fiscal_year', 'key_label': 'lambda',
                 'options': {'func': lambda: yr}},
                {'label': 'fiscal_month', 'key_label': 'lambda',
                 'options': {'func': lambda: mo}},
                {'label': 'bank_account', 'key_label': 'lambda',
                 'options': {'func': lambda: ba['acct']}},
                {'label': 'subsidiary', 'key_label': 'lambda',
                 'options': {'func': lambda: ba['sub']}},
                {'label': 'bank_name', 'key_label': 'lambda',
                 'options': {'func': lambda: ba['bank']}},
                {'label': 'account_type', 'key_label': 'lambda',
                 'options': {'func': lambda: ba['type']}},
                {'label': 'description', 'key_label': 'custom_list',
                 'options': {'values': TXN_DESCS.get(ba['type'], TXN_DESCS['OPERATING'])}},
                {'label': 'reference', 'key_label': 'character_sequence',
                 'options': {'pattern': "REF-%%%%-########"}},
                {'label': '_is_inflow', 'key_label': 'lambda',
                 'options': {'func': lambda: random.random() < 0.45}},
                {'label': '_amount', 'key_label': 'number',
                 'options': {'min': 1000, 'max': 5000000, "decimals": 2}},
                {'label': 'debit_amount', 'key_label': 'lambda',
                 'options': {'func': lambda row:  0 if row['_is_inflow'] else row['_amount']}},
                {'label': 'credit_amount', 'key_label': 'lambda',
                 'options': {'func': lambda row:  row['_amount'] if row['_is_inflow'] else 0}},
                {'label': 'net_amount', 'key_label': 'lambda',
                 'options': {'func': lambda row:  row['_amount'] if row['_is_inflow'] else -row['_amount']}},
                {'label': 'running_balance', 'key_label': 'lambda',
                 'options': {'func': lambda row:  running_bal + row['_amount'] if row['_is_inflow'] else running_bal - row['_amount']}},
                {'label': 'currency', 'key_label': 'lambda',
                 'options': {'func': lambda: 'PHP'}},
                {'label': 'cf_category', 'key_label': 'lambda',
                 'options': {'func': lambda: 'Operating' if ba['type'] in ('OPERATING', 'PAYROLL') else 'Financing'}},
            ]

            rows.append(IkiDataGenerator(schema).one())

df = pd.DataFrame(rows)
df = df.drop(columns=['_bank_ref', '_is_inflow', '_amount'])
df.to_csv(output_path, index=False)
print(
    f"Generated {len(df):,} bank statement rows → data/banking/raw_bank_statements.csv")
