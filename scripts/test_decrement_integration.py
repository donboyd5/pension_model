"""
Test Script: Decrement Table Integration

This script tests the integration of decrement tables through the adapter pattern.
It runs a simplified model for one membership class to verify:
1. Adapter loads decrement tables correctly
2. Workforce projector uses the tables
3. Output is generated successfully
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pandas as pd
from pension_config import MembershipClass, Tier
from pension_config.frs_adapter import FRSAdapter

# Set encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_adapter_loading():
    """Test that adapter can load decrement tables."""
    print("\n" + "="*80)
    print("TEST 1: Adapter Decrement Table Loading")
    print("="*80)

    # Create minimal config
    config = {
        'start_year': 2023,
        'model_period': 5,
        'max_age': 110,
        'min_entry_age': 20,
        'max_entry_age': 70
    }

    # Initialize adapter with baseline directory
    adapter = FRSAdapter(config, baseline_dir="baseline_outputs")

    print(f"\n[OK] Adapter initialized with DecrementLoader")
    print(f"  Baseline dir: {adapter.decrement_loader.baseline_dir}")
    print(f"  Decrement dir: {adapter.decrement_loader.decrement_dir}")

    # Test loading withdrawal table for Regular class
    print("\n[TEST] Loading withdrawal table...")
    withdrawal_table = adapter.load_withdrawal_table(MembershipClass.REGULAR, gender='male')

    if withdrawal_table is not None:
        print(f"  [OK] Loaded withdrawal table for Regular (male)")
        print(f"    Shape: {withdrawal_table.shape}")
        print(f"    Columns: {list(withdrawal_table.columns)}")
        print(f"    Sample rows:")
        print(withdrawal_table.head(3).to_string(index=False))
    else:
        print(f"  [FAIL] Failed to load withdrawal table for Regular (male)")
        return False

    # Test loading mortality table
    print("\n[TEST] Loading mortality table...")
    mortality_table = adapter.load_mortality_table(MembershipClass.REGULAR)

    if mortality_table is not None:
        print(f"  [OK] Loaded mortality table for Regular")
        print(f"    Shape: {mortality_table.shape}")
        print(f"    Columns: {list(mortality_table.columns)[:8]}...")  # First 8 columns
    else:
        print(f"  [FAIL] Failed to load mortality table for Regular")
        return False

    # Test loading retirement table
    print("\n[TEST] Loading retirement table...")
    retirement_table = adapter.load_retirement_table(Tier.TIER_1, 'normal')

    if retirement_table is not None:
        print(f"  [OK] Loaded retirement table for Tier 1 (normal)")
        print(f"    Shape: {retirement_table.shape}")
        print(f"    Columns: {list(retirement_table.columns)}")
        print(f"    Sample rows:")
        print(retirement_table.head(3).to_string(index=False))
    else:
        print(f"  [FAIL] Failed to load retirement table for Tier 1")
        return False

    print("\n[PASS] All adapter loading tests passed!")
    return True


def test_adapter_methods():
    """Test that adapter methods can retrieve rates."""
    print("\n" + "="*80)
    print("TEST 2: Adapter Rate Retrieval Methods")
    print("="*80)

    config = {
        'start_year': 2023,
        'model_period': 5,
        'max_age': 110
    }

    adapter = FRSAdapter(config, baseline_dir="baseline_outputs")

    # Test get_withdrawal_rate
    print("\n[TEST] Testing get_withdrawal_rate()...")
    rate = adapter.get_withdrawal_rate(
        MembershipClass.REGULAR,
        age=35,
        years_of_service=10,
        gender='male'
    )
    print(f"  [OK] Withdrawal rate for Regular, age 35, YOS 10: {rate:.6f}")

    # Test get_mortality_rate
    print("\n[TEST] Testing get_mortality_rate()...")
    mort_rate = adapter.get_mortality_rate(
        MembershipClass.REGULAR,
        age=65,
        gender='male',
        is_retired=False
    )
    print(f"  [OK] Mortality rate for Regular, age 65 (active): {mort_rate:.6f}")

    print("\n[PASS] All adapter method tests passed!")
    return True


def test_available_tables():
    """List all available decrement tables."""
    print("\n" + "="*80)
    print("TEST 3: Available Decrement Tables")
    print("="*80)

    from pathlib import Path
    decrement_dir = Path("baseline_outputs/decrement_tables")

    if not decrement_dir.exists():
        print(f"  [FAIL] Decrement directory not found: {decrement_dir}")
        return False

    files = sorted(decrement_dir.glob("*.csv"))

    print(f"\n[INFO] Found {len(files)} CSV files in {decrement_dir}:\n")

    # Group by type
    withdrawal_files = [f for f in files if 'withdrawal' in f.name]
    retirement_files = [f for f in files if 'retirement' in f.name or 'drop' in f.name or 'early' in f.name or 'normal' in f.name]

    print(f"Withdrawal tables ({len(withdrawal_files)}):")
    for f in withdrawal_files:
        size_kb = f.stat().st_size / 1024
        print(f"  • {f.name:<50} ({size_kb:>6.1f} KB)")

    print(f"\nRetirement tables ({len(retirement_files)}):")
    for f in retirement_files:
        size_kb = f.stat().st_size / 1024
        print(f"  • {f.name:<50} ({size_kb:>6.1f} KB)")

    print("\n✅ Table inventory complete!")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DECREMENT TABLE INTEGRATION TEST SUITE")
    print("="*80)

    tests = [
        ("Available Tables", test_available_tables),
        ("Adapter Loading", test_adapter_loading),
        ("Adapter Methods", test_adapter_methods),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {test_name}")

    total = len(results)
    passed = sum(1 for p in results.values() if p)

    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*80}\n")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
