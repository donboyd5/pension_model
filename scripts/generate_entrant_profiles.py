"""Generate entrant profile files from workforce data to match R model."""
import pandas as pd
from pathlib import Path

def generate_entrant_profiles():
    """Generate entrant profile files for all classes."""
    baseline_dir = Path("baseline_outputs")
    classes = ["regular", "special", "admin", "eco", "eso", "judges", "senior_management"]

    for class_name in classes:
        # Load workforce active data
        wf_file = baseline_dir / f"{class_name}_wf_active.csv"
        if not wf_file.exists():
            print(f"Workforce file not found: {wf_file}")
            continue

        wf_df = pd.read_csv(wf_file)

        # Filter to most recent entry year
        max_entry_year = wf_df['year'].max()
        recent_wf = wf_df[wf_df['year'] == max_entry_year]

        # Calculate entry_age from age - yos
        recent_wf = recent_wf.copy()
        recent_wf['entry_age_calc'] = recent_wf['age'] - recent_wf['entry_age']

        # Group by entry_age and get count
        entrant_profile = recent_wf.groupby('entry_age_calc').agg(
            count=('n_active', 'sum')
        ).reset_index()

        # Calculate distribution
        total_count = entrant_profile['count'].sum()
        entrant_profile['entrant_dist'] = entrant_profile['count'] / total_count

        # Rename column to match expected format
        entrant_profile = entrant_profile.rename(columns={'entry_age_calc': 'entry_age'})

        # Save to file
        output_file = baseline_dir / f"{class_name}_entrant_profile.csv"
        entrant_profile.to_csv(output_file, index=False)
        print(f"Generated {output_file}: {len(entrant_profile)} rows")


if __name__ == "__main__":
    generate_entrant_profiles()
