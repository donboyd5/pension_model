"""
Standalone test to verify new entrant calculation logic is correct.
Tests the formula directly without importing the full module chain.
"""

print("="*80)
print("NEW ENTRANT CALCULATION - FORMULA VERIFICATION")
print("="*80)

print("\n1. R MODEL FORMULA (utility_functions.R line 181):")
print("   ne = sum(wf1)*(1 + g) - sum(wf2)")
print("   where:")
print("     wf1 = workforce BEFORE decrements (separations)")
print("     wf2 = workforce AFTER decrements")
print("     g = population growth rate")

def r_model_new_entrants(pre_decrement, post_decrement, growth):
    """R model formula for new entrants."""
    return pre_decrement * (1 + growth) - post_decrement

def old_python_new_entrants(post_decrement, growth):
    """OLD Python model (buggy)."""
    target = post_decrement * (1 + growth)
    return target - post_decrement

print("\n2. TEST SCENARIOS:")
print("="*80)

scenarios = [
    {"name": "Zero Growth (R Baseline)", "pre": 100000, "sep": 5000, "growth": 0.0},
    {"name": "2% Growth", "pre": 100000, "sep": 5000, "growth": 0.02},
    {"name": "Negative Growth", "pre": 100000, "sep": 5000, "growth": -0.01},
]

for scenario in scenarios:
    pre = scenario["pre"]
    sep = scenario["sep"]
    post = pre - sep
    growth = scenario["growth"]

    r_result = r_model_new_entrants(pre, post, growth)
    old_py_result = old_python_new_entrants(post, growth)

    print(f"\nScenario: {scenario['name']}")
    print(f"  Pre-decrement workforce: {pre:,}")
    print(f"  Separations: {sep:,}")
    print(f"  Post-decrement workforce: {post:,}")
    print(f"  Growth rate: {growth:.1%}")
    print(f"")
    print(f"  R Model new entrants: {r_result:,.0f}")
    print(f"  Old Python new entrants: {old_py_result:,.0f}")
    print(f"  Difference: {r_result - old_py_result:,.0f}")
    print(f"  Final population R: {post + r_result:,.0f}")
    print(f"  Final population Old Python: {post + old_py_result:,.0f}")

print("\n3. KEY INSIGHT:")
print("="*80)
print("""
With ZERO growth (R baseline):
- R Model: new_entrants = pre - post = EXACT REPLACEMENT for separations
  Result: Population stays CONSTANT

- Old Python: new_entrants = post * (1+0) - post = 0
  Result: Population DECLINES by separation amount each year

This is why Python showed 10-20% declines while R stayed constant!

FIXED in WorkforceProjector.project_year():
- Now tracks pre_decrement_total BEFORE separations
- Passes both pre and post to _calculate_new_entrants()
- Uses R formula exactly
""")

print("\n4. VALIDATION STATUS:")
print("="*80)
print("""
[x] ESO withdrawal table mapping fixed (uses Regular rates)
[x] New entrant calculation formula matches R model
[x] Core WorkforceProjector logic corrected

[NEXT] Need to test actual WorkforceProjector with real data
       (Current validation script uses simplified logic, not WorkforceProjector)
""")
