import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("dbt/seeds")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fx_path = OUTPUT_DIR / "chart_of_accounts.csv"

rows = [
    # ── Balance Sheet: Assets ──────────────────────────────────────────────
    ('1001', 'Cash & Cash Equivalents',         'Asset',
     'Current Assets',           'BS', 'Debit',  10, True),
    ('1002', 'Accounts Receivable',             'Asset',
     'Current Assets',           'BS', 'Debit',  20, True),
    ('1003', 'Inventory',                       'Asset',
     'Current Assets',           'BS', 'Debit',  30, True),
    ('1004', 'Property, Plant & Equipment',     'Asset',
     'Non-Current Assets',       'BS', 'Debit',  40, True),
    # ── Balance Sheet: Liabilities ────────────────────────────────────────
    ('2001', 'Accounts Payable',                'Liability',
     'Current Liabilities',      'BS', 'Credit', 50, True),
    ('2002', 'Short-Term Loans',                'Liability',
     'Current Liabilities',      'BS', 'Credit', 60, True),
    ('2003', 'Long-Term Debt',                  'Liability',
     'Non-Current Liabilities',  'BS', 'Credit', 70, True),
    # ── Balance Sheet: Equity ─────────────────────────────────────────────
    ('3001', 'Share Capital',                   'Equity',
     'Equity',                   'BS', 'Credit', 80, True),
    ('3002', 'Retained Earnings',               'Equity',
     'Equity',                   'BS', 'Credit', 90, True),
    # ── Income Statement: Revenue ─────────────────────────────────────────
    ('4001', 'Revenue - Retail',                'Revenue',
     'Net Revenue',              'IS', 'Credit', 100, True),
    ('4002', 'Revenue - Services',              'Revenue',
     'Net Revenue',              'IS', 'Credit', 110, True),
    ('4003', 'Revenue - Freight',               'Revenue',
     'Net Revenue',              'IS', 'Credit', 120, True),
    ('4004', 'Revenue - Rental',                'Revenue',
     'Net Revenue',              'IS', 'Credit', 130, True),
    # ── Income Statement: COGS ────────────────────────────────────────────
    ('5001', 'Cost of Goods Sold',              'COGS',
     'COGS',                     'IS', 'Debit',  200, True),
    ('5002', 'Direct Labor',                    'COGS',
     'COGS',                     'IS', 'Debit',  210, True),
    ('5003', 'Freight & Logistics Cost',        'COGS',
     'COGS',                     'IS', 'Debit',  220, True),
    # ── Income Statement: Operating Expenses ──────────────────────────────
    ('6001', 'Salaries & Wages',                'OpEx',
     'Personnel Costs',          'IS', 'Debit',  300, True),
    ('6002', 'Rent & Utilities',                'OpEx',
     'Occupancy',                'IS', 'Debit',  310, True),
    ('6003', 'Marketing & Advertising',         'OpEx',
     'Marketing',                'IS', 'Debit',  320, True),
    ('6004', 'Depreciation & Amortization',     'OpEx',
     'D&A',                      'IS', 'Debit',  330, True),
    ('6005', 'Professional Fees',               'OpEx',
     'Admin & General',          'IS', 'Debit',  340, True),
    ('6006', 'Travel & Entertainment',          'OpEx',
     'Admin & General',          'IS', 'Debit',  350, True),
    ('6007', 'IT & Communications',             'OpEx',
     'Admin & General',          'IS', 'Debit',  360, True),
    # ── Income Statement: Finance Costs ───────────────────────────────────
    ('7001', 'Interest Expense',                'Finance Cost',
     'Finance Costs',            'IS', 'Debit',  400, True),
    ('7002', 'Bank Charges',                    'Finance Cost',
     'Finance Costs',            'IS', 'Debit',  410, True),
    # ── Income Statement: Tax ─────────────────────────────────────────────
    ('8001', 'Income Tax Expense',              'Tax',
     'Tax',                      'IS', 'Debit',  500, True),
]

df = pd.DataFrame(rows, columns=[
    'gl_account_code', 'account_name', 'account_type',
    'pnl_line', 'financial_statement', 'normal_balance',
    'sort_order', 'is_active',
])
df.to_csv(fx_path, index=False)
print(f"Generated {len(df)} accounts → dbt/seeds/chart_of_accounts.csv")
