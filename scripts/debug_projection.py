"""
Debug script to trace through workforce projection.
"""
import pandas as pd
import numpy as np

# Load separation table
sep_df = pd.read_csv('baseline_outputs/separation_tables/separation_admin.csv')
print(f'Separation table shape: {sep_df.shape}')
print(f'Separation table columns: {sep_df.columns.tolist()}')

# Check for unique combinations
keys = ['entry_year', 'entry_age', 'term_age']
unique_keys = sep_df.groupby(keys).size()
print(f'\nUnique key combinations: {len(unique_keys)}')
print(f'Total rows: {len(sep_df)}')

# Check if yos = term_age - entry_age always
sep_df['calc_yos'] = sep_df['term_age'] - sep_df['entry_age']
mismatch = sep_df[sep_df['yos'] != sep_df['calc_yos']]
print(f'\nYOS mismatches: {len(mismatch)}')
if len(mismatch) > 0:
    print(mismatch.head())

# Load initial workforce
wf_df = pd.read_csv('baseline_outputs/admin_wf_active.csv')
print(f'\nWorkforce table shape: {wf_df.shape}')
print(f'Workforce columns: {wf_df.columns.tolist()}')

# Get year 2022 data
wf_2022 = wf_df[wf_df['year'] == 2022]
print(f'\nYear 2022 workforce shape: {wf_2022.shape}')
print(f'Total active in 2022: {wf_2022["n_active"].sum()}')

# Test separation rate lookup for a sample
entry_year = 1995
entry_age = 30
term_age = 35
yos = term_age - entry_age

match = sep_df[(sep_df['entry_year'] == entry_year) &
               (sep_df['entry_age'] == entry_age) &
               (sep_df['term_age'] == term_age)]

print(f'\n=== Lookup Test ====')
print(f'entry_year={entry_year}, entry_age={entry_age}, term_age={term_age}, yos={yos}')
print(f'Matches found: {len(match)}')
if len(match) > 0:
    print(match[['entry_year', 'entry_age', 'term_age', 'yos', 'tier', 'separation_rate']])
else:
    print('No match found!')

# Check what entry ages exist in separation table
print(f'\n=== Entry ages in separation table ====')
print(f'Min entry_age: {sep_df["entry_age"].min()}')
print(f'Max entry_age: {sep_df["entry_age"].max()}')
print(f'Unique entry ages: {sorted(sep_df["entry_age"].unique())}')

# Check what entry ages exist in workforce
print(f'\n=== Entry ages in workforce ====')
print(f'Min entry_age: {wf_2022["entry_age"].min()}')
print(f'Max entry_age: {wf_2022["entry_age"].max()}')
print(f'Unique entry ages: {sorted(wf_2022["entry_age"].unique())}')
