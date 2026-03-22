# step2.py
import numpy as np
import pulp
import os

save_dir = "C:/Users/vipon/Downloads/Ambulance"

# ── 1. Load Data ──────────────────────────────────────────────
travel_matrix = np.load(os.path.join(save_dir, "travel_matrix.npy"))
staging_names = np.load(os.path.join(save_dir, "staging_list.npy"), allow_pickle=True)
demand_names  = np.load(os.path.join(save_dir, "demand_list.npy"),  allow_pickle=True)

n_demand  = len(demand_names)
n_staging = len(staging_names)

print("Demand nodes:", n_demand)
print("Staging locations:", n_staging)

# ── 2. Load All 35 Combined Matrices ─────────────────────────
days    = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
periods = ["night","morning","midday","evening","late"]

combined_matrices = {}
for day in days:
    for period in periods:
        key = f"{day}_{period}"
        combined_matrices[key] = np.load(
            os.path.join(save_dir, f"travel_matrix_{key}.npy")
        )

print(f"Loaded {len(combined_matrices)} combined matrices")

# ── 3. Coverage Matrix ────────────────────────────────────────
COVERAGE_THRESHOLD = 8.0

coverage = {}
for key, matrix in combined_matrices.items():
    coverage[key] = (matrix <= COVERAGE_THRESHOLD).astype(int)

# ── 4. MCLP Solver ────────────────────────────────────────────
def solve_mclp(cov_matrix, n_ambulances, label):
    n_dem, n_sta = cov_matrix.shape

    prob = pulp.LpProblem(f"MCLP_{label}", pulp.LpMaximize)

    x = [pulp.LpVariable(f"x_{j}", cat="Binary") for j in range(n_sta)]
    y = [pulp.LpVariable(f"y_{i}", cat="Binary") for i in range(n_dem)]

    prob += pulp.lpSum(y[i] for i in range(n_dem))

    for i in range(n_dem):
        prob += y[i] <= pulp.lpSum(cov_matrix[i, j] * x[j] for j in range(n_sta))

    prob += pulp.lpSum(x[j] for j in range(n_sta)) <= n_ambulances

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    staged  = [str(staging_names[j]) for j in range(n_sta) if pulp.value(x[j]) == 1]
    covered = sum(pulp.value(y[i]) for i in range(n_dem))
    pct     = covered / n_dem * 100

    return staged, covered, pct

# ── 5. Solve All 35 Combinations ─────────────────────────────
TARGET_COVERAGE = 85.0

print("Solving MCLP for all 35 day/period combinations...")

results = {}
for key in combined_matrices.keys():
    cov = coverage[key]
    for n_amb in range(1, n_staging + 1):
        staged, covered, pct = solve_mclp(cov, n_amb, key)
        if pct >= TARGET_COVERAGE:
            break
    results[key] = {
        "ambulances": n_amb,
        "staged_at":  staged,
        "coverage":   pct
    }

print("Done!")

# ── 6. Fleet Size Summary Table ───────────────────────────────
print("\n--- Fleet Size by Day and Period ---\n")
print(f"{'':12} {'night':>8} {'morning':>8} {'midday':>8} {'evening':>8} {'late':>8}")
print("-" * 55)

for day in days:
    row = f"{day.upper():12}"
    for period in periods:
        key = f"{day}_{period}"
        row += f" {results[key]['ambulances']:>8}"
    print(row)

max_fleet = max(r["ambulances"] for r in results.values())
print(f"\nRecommended fleet size: {max_fleet} ambulances")

hardest = max(results.items(), key=lambda x: x[1]["ambulances"])
easiest = min(results.items(), key=lambda x: x[1]["ambulances"])
print(f"Hardest period : {hardest[0]} ({hardest[1]['ambulances']} amb, {hardest[1]['coverage']:.1f}%)")
print(f"Easiest period : {easiest[0]} ({easiest[1]['ambulances']} amb, {easiest[1]['coverage']:.1f}%)")

# ── 7. Staging Locations by Day and Period ────────────────────
print("\n--- Where to Stage Ambulances ---\n")
for day in days:
    print(f"{day.upper()}")
    for period in periods:
        key     = f"{day}_{period}"
        staged  = results[key]["staged_at"]
        pct     = results[key]["coverage"]
        n       = results[key]["ambulances"]
        stations = ", ".join(staged)
        print(f"  {period:10s} ({n} amb, {pct:.0f}%): {stations}")
    print()

# ── 8. Permanently Uncovered Nodes ───────────────────────────
print("\n--- Permanently Uncovered Nodes ---")
never_covered = []
for i, name in enumerate(demand_names):
    covered_any = any(
        combined_matrices[key][i].min() <= 8.0
        for key in combined_matrices
    )
    if not covered_any:
        min_ever = min(combined_matrices[key][i].min() for key in combined_matrices)
        never_covered.append((name, min_ever))

if never_covered:
    for name, t in never_covered:
        print(f"  {name}: best possible time = {t:.1f} min")
else:
    print("  All nodes coverable in at least one period!")

# ── 9. 12-Minute Maximum Check ────────────────────────────────
print("\n--- 12-Minute Maximum Check ---")
violations = []
for day in days:
    for period in periods:
        key       = f"{day}_{period}"
        matrix    = combined_matrices[key]
        min_times = matrix.min(axis=1)
        over_12   = (min_times > 12.0).sum()
        worst     = min_times.max()
        if over_12 > 0:
            violations.append((key, over_12, worst))

if violations:
    print(f"  {'Period':<30} {'Nodes>12min':>12} {'Worst':>8}")
    print(f"  {'-'*30} {'-'*12} {'-'*8}")
    for key, count, worst in violations:
        print(f"  {key:<30} {count:>12} {worst:>7.1f} min")
else:
    print("  All nodes within 12 minutes!")