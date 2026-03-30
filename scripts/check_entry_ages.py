"""Check entry ages in workforce data for all classes."""
import pandas as pd
from pathlib import Path

baseline_dir = Path("baseline_outputs")
classes = ["regular", "special", "admin", "eco", "eso", "judges", "senior_management"]

print("Entry ages in workforce data:")
for class_name in classes:
    wf_file = baseline_dir / f"{class_name}_wf_active.csv"
    if wf_file.exists():
        df = pd.read_csv(wf_file)
        entry_ages = sorted(df['entry_age'].unique().tolist())
        print(f"  {class_name}: {entry_ages}")
    else:
        print(f"  {class_name}: FILE NOT FOUND")
