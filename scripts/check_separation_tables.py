"""Check separation tables for failing classes.

This script checks the pre-computed separation tables for failing classes
to understand why they have declining populations.
"""

import pandas as pd
from pathlib import Path

# Classes with separation tables
CLASSES = ['admin', 'eco', 'eso', 'judges', 'senior_management']

# Directory containing separation tables
SEP_TABLES_DIR = Path('baseline_outputs/separation_tables')

def check_separation_tables():
    """Check separation tables for failing classes."""
    results = {}

    for class_name in CLASSES:
        sep_file = SEP_TABLES_DIR / f"separation_{class_name}.csv"

        if not sep_file.exists():
            print(f"  Separation table for {class_name} NOT FOUND")
            results[class_name] = "NOT_FOUND"
            continue

        # Load separation table
        sep_df = pd.read_csv(sep_file)

        # Check sample rates
        print(f"\n  Sample separation rates for {class_name}:")
        sample = sep_df[(sep_df['entry_year'] == 2022) & (sep_df['entry_age'] == 25) & (sep_df['term_age'] == 55)]
        print(sample.head(10))

        # Check rates for vested members (should use withdrawal rates)
        vested_mask = sep_df['tier'].str.contains('vested')
        vested_df = sep_df[vested_mask]

        print(f"\n  Vested separation rates for {class_name} (should use withdrawal rates):")
        print(vested_df['separation_rate'].describe())
        print("\n  Vested tier counts:")
        print(vested_df['tier'].value_counts())

        results[class_name] = {
            'sample_rate': sample['separation_rate'].iloc[0] if len(sample) > 0 else 0.0,
            'vested_rates': vested_df['separation_rate'].describe() if len(vested_df) > 0 else None,
            'vested_tier_counts': vested_df['tier'].value_counts().to_dict() if len(vested_df) > 0 else {}
        }


if __name__ == "__main__":
    check_separation_tables()
