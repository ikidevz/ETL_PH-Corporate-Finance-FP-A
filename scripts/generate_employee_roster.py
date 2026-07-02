import random
import pandas as pd
from pathlib import Path
from ikidatagen import IkiDataGenerator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
output_path = DATA_DIR / "hr/raw_employee_roster.csv"

COST_CENTERS = [
    'CC-RETAIL-MNL', 'CC-RETAIL-CEB', 'CC-RETAIL-DAV',
    'CC-LOGISTICS',  'CC-FINANCE',    'CC-MKTG',
    'CC-HR',         'CC-IT',         'CC-OPS-MNL',
    'CC-SHARED-SVC',
]
SUBSIDIARIES = ['SUB_A', 'SUB_B', 'SUB_C', 'SUB_D', 'SUB_E']
JOB_LEVELS = ['Staff', 'Senior', 'Manager', 'Director', 'VP']
EMPLOYMENT_STATUS = ['ACTIVE', 'ACTIVE', 'ACTIVE',
                     'ACTIVE', 'TERMINATED']

HEADCOUNT = random.randint(200, 500)
schema = [
    {'label': 'employee_id', 'key_label': 'character_sequence',
     'options': {'pattern': "EMP-%%%%-########"}},
    'full_name',
    {'label': 'cost_center', 'key_label': 'custom_list',
     'options': {'values': COST_CENTERS}},
    {'label': 'subsidiary', 'key_label': 'custom_list',
     'options': {'values': SUBSIDIARIES}},
    {'label': 'job_level', 'key_label': 'lambda',
     'options': {'func': lambda: random.choices(JOB_LEVELS, weights=[35, 30, 20, 12, 3])[0]}},
    {"label": "monthly_base_php", "key_label": "number", "options": {
        "min": 20000, "max": 250000, "decimals": 2
    }},
    {"label": "hire_date", "key_label": "datetime", "options": {
        "from_date": '1/1/2018', "to_date": '06/30/2026', "date_format": "yyyy-mm-dd"
    }},
    {"label": "_termination_date", "key_label": "datetime", "options": {
        "from_date": '1/1/2018', "to_date": '06/30/2026', "date_format": "yyyy-mm-dd"
    }},
    {'label': '_status', 'key_label': 'custom_list',
     'options': {'values': EMPLOYMENT_STATUS}},
    {'label': 'termination_date', 'key_label': 'lambda',
     'options': {'func': lambda row: row['_termination_date'] if row['_status'] else None}},
    {'label': 'employment_status', 'key_label': 'lambda',
     'options': {'func': lambda row:  row['_status']}},
]

payload = IkiDataGenerator(schema).many(HEADCOUNT).data
df = pd.DataFrame(payload)
df = df.drop(columns=['_termination_date', '_status'])
df.to_csv(output_path, index=False)
print(f"Generated {HEADCOUNT:,} employment roster → {output_path}")
