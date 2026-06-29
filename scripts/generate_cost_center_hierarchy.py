import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("dbt/seeds")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fx_path = OUTPUT_DIR / "cost_center_hierarchy.csv"

rows = [
    ('CC-RETAIL-MNL',  'Retail Manila',          'Retail',
     'Commercial',   'SUB_A', 'Retail',         'PHP', True),
    ('CC-RETAIL-CEB',  'Retail Cebu',            'Retail',
     'Commercial',   'SUB_B', 'Retail',         'PHP', True),
    ('CC-RETAIL-DAV',  'Retail Davao',           'Retail',
     'Commercial',   'SUB_C', 'Retail',         'PHP', True),
    ('CC-LOGISTICS',   'Logistics & Fulfillment', 'Operations',
     'Supply Chain', 'SUB_A', 'Logistics',      'PHP', True),
    ('CC-FINANCE',     'Finance & Accounting',    'Finance',
     'Corporate',    'SUB_A', 'Holding',        'PHP', True),
    ('CC-MKTG',        'Marketing',               'Marketing',
     'Commercial',   'SUB_B', 'Retail',         'PHP', True),
    ('CC-HR',          'Human Resources',         'HR',
     'Corporate',    'SUB_A', 'Holding',        'PHP', True),
    ('CC-IT',          'IT & Systems',            'IT',
     'Corporate',    'SUB_A', 'Holding',        'PHP', True),
    ('CC-OPS-MNL',     'Operations Manila',       'Operations',
     'Supply Chain', 'SUB_D', 'Manufacturing',  'PHP', True),
    ('CC-SHARED-SVC',  'Shared Services',         'Shared Svc',
     'Corporate',    'SUB_E', 'Services',       'PHP', True),
]

df = pd.DataFrame(rows, columns=[
    'cost_center_code', 'cost_center_name', 'department', 'division',
    'subsidiary_code', 'subsidiary_name', 'reporting_currency', 'is_active',
])

# Add industry column derived from subsidiary
industry_map = {
    'SUB_A': 'Holding',
    'SUB_B': 'Retail',
    'SUB_C': 'Retail',
    'SUB_D': 'Manufacturing',
    'SUB_E': 'Services',
}
df['industry'] = df['subsidiary_code'].map(industry_map)

df.to_csv(fx_path, index=False)
print(
    f"Generated {len(df)} cost centers → fpna_dbt/seeds/cost_center_hierarchy.csv")
