"""Quick test to verify ESO withdrawal table mapping fix."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pension_data.decrement_loader import DecrementLoader

loader = DecrementLoader("baseline_outputs")

print("Testing ESO withdrawal table loading...")
print(f"WITHDRAWAL_CLASS_MAP['eso'] = {loader.WITHDRAWAL_CLASS_MAP.get('eso')}")

# Try loading ESO table
eso_table = loader.load_withdrawal_table("eso", gender="male")

if eso_table is not None:
    print(f"\n[OK] ESO table loaded successfully!")
    print(f"  Shape: {eso_table.shape}")
    print(f"  Columns: {list(eso_table.columns)}")
    print(f"  Sample rate at age 30, YOS 5:")
    sample = eso_table[(eso_table['age'] == 30) & (eso_table['yos'] == 5)]
    if len(sample) > 0:
        print(f"    {sample['withdrawal_rate'].iloc[0]:.6f}")
else:
    print(f"\n[FAIL] ESO table NOT loaded")
    print("Checking if regular_male table exists...")
    from pathlib import Path
    reg_path = Path("baseline_outputs/decrement_tables/withdrawal_regular_male.csv")
    print(f"  withdrawal_regular_male.csv exists: {reg_path.exists()}")
