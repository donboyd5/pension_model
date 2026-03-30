"""Debug separation rate lookup for admin class."""
import pandas as pd
from pathlib import Path

# Load admin workforce and separation table
baseline_dir = Path("baseline_outputs")
wf = pd.read_csv(baseline_dir / "admin_wf_active.csv")
sep = pd.read_csv(baseline_dir / "separation_tables" / "separation_admin.csv")

# Filter workforce to year 2022
wf_2022 = wf[wf['year'] == 2022].copy()
wf_2022['yos'] = wf_2022['age'] - wf_2022['entry_age']
wf_2022['entry_year'] = 2022 - wf_2022['yos']

print("Workforce 2022 sample (with n_active > 0):")
print(wf_2022[wf_2022['n_active'] > 0].head(20).to_string())

print("\n\nSeparation table entry_year range:", sep['entry_year'].min(), "-", sep['entry_year'].max())
print("Separation table entry_age values:", sorted(sep['entry_age'].unique()))

# Try to look up separation rates for the first few rows with n_active > 0
print("\n\nSeparation rate lookups:")
for idx, row in wf_2022[wf_2022['n_active'] > 0].head(10).iterrows():
    entry_year = row['entry_year']
    entry_age = row['entry_age']
    term_age = row['age']
    yos = row['yos']

    mask = (
        (sep['entry_year'] == entry_year) &
        (sep['entry_age'] == entry_age) &
        (sep['term_age'] == term_age) &
        (sep['yos'] == yos)
    )
    matches = sep[mask]

    if len(matches) > 0:
        sep_rate = matches.iloc[0]['separation_rate']
        print(f"  entry_year={entry_year}, entry_age={entry_age}, age={term_age}, yos={yos}: sep_rate={sep_rate}")
    else:
        print(f"  entry_year={entry_year}, entry_age={entry_age}, age={term_age}, yos={yos}: NO MATCH FOUND")

        # Try to find why no match
        # Check if entry_year exists
        ey_match = sep[sep['entry_year'] == entry_year]
        if len(ey_match) == 0:
            print(f"    -> entry_year {entry_year} not in separation table")
        else:
            ea_match = ey_match[ey_match['entry_age'] == entry_age]
            if len(ea_match) == 0:
                print(f"    -> entry_age {entry_age} not in separation table for entry_year {entry_year}")
