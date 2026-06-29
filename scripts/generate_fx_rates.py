import pandas as pd
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path("dbt/seeds")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fx_path = OUTPUT_DIR / "fx_rates.csv"

BSP_RATES = [
    # FY2023 (PHP depreciated steadily, range ≈ 54.78–56.79)
    (2023,  1, 54.9913),
    (2023,  2, 54.7831),
    (2023,  3, 54.7956),
    (2023,  4, 55.3155),
    (2023,  5, 55.7279),
    (2023,  6, 55.8946),
    (2023,  7, 54.9211),
    (2023,  8, 56.1599),
    (2023,  9, 56.7869),
    (2023, 10, 56.7889),
    (2023, 11, 55.8122),
    (2023, 12, 55.5877),
    # FY2024 (further depreciation, range ≈ 55.85–58.70)
    (2024,  1, 55.9723),
    (2024,  2, 56.0649),
    (2024,  3, 55.8493),
    (2024,  4, 56.9506),
    (2024,  5, 57.7619),
    (2024,  6, 58.6963),
    (2024,  7, 58.4845),
    (2024,  8, 57.1935),
    (2024,  9, 56.0713),
    (2024, 10, 57.3009),
    (2024, 11, 58.6947),
    (2024, 12, 58.4480),
    # FY2025 (modest recovery mid-year, range ≈ 55.62–58.91)
    (2025,  1, 58.3906),
    (2025,  2, 58.0942),
    (2025,  3, 57.4246),
    (2025,  4, 56.8529),
    (2025,  5, 55.6246),
    (2025,  6, 56.3586),
    (2025,  7, 56.7523),
    (2025,  8, 57.2525),
    (2025,  9, 57.2501),
    (2025, 10, 58.2984),
    (2025, 11, 58.9136),
    (2025, 12, 58.8488),

    (2026, 1, 59.1622),
    (2026, 2, 58.2803),
    (2026, 3, 59.4069),
    (2026, 4, 60.2913),
    (2026, 5, 61.4410),
    (2026, 6, 61.28)
]

rows = []
for fy, mo, rate in BSP_RATES:
    rows.append({
        'fiscal_year':   fy,
        'fiscal_month':  mo,
        'period_name':   f'{fy}-{mo:02d}',
        'from_currency': 'USD',
        'to_currency':   'PHP',
        'usd_php_rate':  rate,
        'source':        'BSP',  # Bangko Sentral ng Pilipinas
    })

df = pd.DataFrame(rows)
df.to_csv(fx_path, index=False)
print(f"Generated {len(df)} FX rate rows → dbt/seeds/fx_rates.csv")
