import numpy as np
import simpy
import random
import os
from collections import defaultdict

save_dir = "C:/Users/vipon/Downloads/Ambulance"

# ── 1. Load Data ──────────────────────────────────────────────
staging_names = np.load(os.path.join(save_dir, "staging_list.npy"), allow_pickle=True)
demand_names  = np.load(os.path.join(save_dir, "demand_list.npy"),  allow_pickle=True)
travel_matrix = np.load(os.path.join(save_dir, "travel_matrix.npy"))

n_demand  = len(demand_names)
n_staging = len(staging_names)

print("Demand nodes:", n_demand)
print("Staging locations:", n_staging)

# ── 2. Load All Combined Matrices ─────────────────────────────
days    = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
periods = ["night","morning","midday","evening","late"]

combined_matrices = {}
for day in days:
    for period in periods:
        key = f"{day}_{period}"
        combined_matrices[key] = np.load(
            os.path.join(save_dir, f"travel_matrix_{key}.npy")
        )

# ── 3. Simulation Parameters ──────────────────────────────────
RANDOM_SEED       = 42
SIM_DAYS          = 730
CALL_RATE_DAILY   = 4.19
ON_SCENE_MEAN     = 18.0
ON_SCENE_STD      = 5.0
TRANSPORT_MEAN    = 15.0
TRANSPORT_STD     = 5.0
RETURN_MEAN       = 12.0
RETURN_STD        = 3.0

# ── Chute Time (dispatch -> enroute) from real WRS data ───────
CHUTE_TIME_MEAN   = 2.0   # minutes — derived from historical d2e records
CHUTE_TIME_STD    = 1.0

CALL_RATE_PER_MIN = CALL_RATE_DAILY / (24 * 60)

dow_multipliers = {
    0: 1.05,  # monday
    1: 0.86,  # tuesday
    2: 1.03,  # wednesday
    3: 0.95,  # thursday
    4: 1.15,  # friday
    5: 1.03,  # saturday
    6: 0.93,  # sunday
}

tod_multipliers = {
    "night":   0.42,
    "morning": 0.41,
    "midday":  1.00,
    "evening": 0.90,
    "late":    0.75,
}

historical_response = {
    "night":   11.9,
    "morning": 15.0,
    "midday":  14.4,
    "evening": 12.6,
    "late":    12.9,
}

print("Parameters loaded.")
print(f"Simulating {SIM_DAYS} days...")

# ── 4. City Mapping ───────────────────────────────────────────
wise_nodes = [
    "Downtown Wise", "Wise County Central High", "Heritage Hall Wise",
    "UVA Wise Campus", "Wise County Sheriff Department",
    "Wise County Animal Hospital", "Wise County Technical School",
    "Lighthouse Family Worship Center", "Warrior Wash", "Hardees Wise",
    "Leonard D Rogers PC", "Lowes Home Improvement", "Wise Municipal Pool",
]
norton_nodes = [
    "Norton City Center", "Norton Community Hospital",
    "Walmart Supercenter Norton", "Wrap Norton", "Ramsey Freewill Baptist",
    "Fishtales", "Cananchee Creek", "Central Free Will Baptist Church",
    "Lincoln Road Coffee Lounge", "CVS Norton", "Cinema City",
    "Jacob Justice", "Snack Shack", "Dollar General Norton",
]
bsg_nodes = [
    "Union High School BSG", "Mountain Empire Community College",
    "Department of Veterans Services", "Trinity Methodist Church",
    "Sunoco Gas Station BSG", "Pizza Plus BSG", "Food Bank Wise County",
    "United States Postal Service BSG", "Bobs Market",
    "Oak Grove Baptist Church", "1339 Wildcat Rd BSG", "Iron Works Fitness",
    "Cavalier Motor Works", "BP Gas Station BSG", "The Pastry Cottage",
    "Lonesome Pine Motorworks", "2241 Carter St BSG", "Dog Shop BSG",
    "Wallens Ridge State Prison",
]

def get_city(demand_name):
    if demand_name in wise_nodes:
        return "Wise"
    elif demand_name in norton_nodes:
        return "Norton"
    elif demand_name in bsg_nodes:
        return "Big Stone Gap"
    else:
        return "Corridor"

# ── 5. Helper Functions ───────────────────────────────────────
def get_period(minute_of_day):
    hour = minute_of_day / 60
    if hour < 5 or hour >= 22:
        return "night"
    elif hour < 9:
        return "morning"
    elif hour < 13:
        return "midday"
    elif hour < 18:
        return "evening"
    else:
        return "late"

def get_day_of_week(sim_minute):
    return int((sim_minute / (24 * 60)) % 7)

def get_call_rate(sim_minute):
    period = get_period(sim_minute % (24 * 60))
    dow    = get_day_of_week(sim_minute)
    return CALL_RATE_PER_MIN * tod_multipliers[period] * dow_multipliers[dow]

def get_travel_time_sim(staging_idx, demand_idx, sim_minute):
    period = get_period(sim_minute % (24 * 60))
    day    = days[get_day_of_week(sim_minute)]
    key    = f"{day}_{period}"
    return combined_matrices[key][demand_idx, staging_idx]

def nearest_available(ambulances, demand_idx, sim_minute):
    best_time = float("inf")
    best_idx  = None
    for idx, amb in enumerate(ambulances):
        if amb["available"]:
            t = get_travel_time_sim(amb["staging"], demand_idx, sim_minute)
            if t < best_time:
                best_time = t
                best_idx  = idx
    return best_idx, best_time

# ── 6. Results Storage ────────────────────────────────────────
results_log = {
    "response_times":       [],
    "no_ambulance":         0,
    "calls_by_period":      defaultdict(int),
    "response_by_period":   defaultdict(list),
    "calls_by_city":        defaultdict(int),
    "response_by_city":     defaultdict(list),
    "city_period_response": defaultdict(list),
    "covered_8":            0,
    "covered_12":           0,
    "total_calls":          0,
}

# ── 7. Staging Plan ───────────────────────────────────────────
staging_plan = {
    "night":   ["Wise Fire Department", "Norton Fire Department",
                "Lonesome Pine Hospital"],
    "morning": ["Wise Fire Department", "Norton Fire Department",
                "BSG Fire Department", "Lonesome Pine Hospital",
                "Norton Community Hospital"],
    "midday":  ["Wise Fire Department", "Norton Fire Department",
                "BSG Fire Department", "Lonesome Pine Hospital",
                "Norton Community Hospital"],
    "evening": ["Wise Fire Department", "Wise Rescue Squad",
                "Norton Fire Department", "Norton Community Hospital",
                "BSG Fire Department", "BSG Rescue Squad",
                "Lonesome Pine Hospital"],
    "late":    ["Wise Fire Department", "Norton Fire Department",
                "Lonesome Pine Hospital"],
}

def get_staging_indices(period):
    stations = staging_plan[period]
    return [i for i, name in enumerate(staging_names) if name in stations]

# ── 8. SimPy Simulation ───────────────────────────────────────
def ambulance_call(env, amb_idx, ambulances, demand_idx, sim_minute):
    chute     = max(0.5, random.gauss(CHUTE_TIME_MEAN, CHUTE_TIME_STD))
    travel    = get_travel_time_sim(ambulances[amb_idx]["staging"], demand_idx, sim_minute)
    on_scene  = max(5,   random.gauss(ON_SCENE_MEAN,  ON_SCENE_STD))
    transport = max(5,   random.gauss(TRANSPORT_MEAN, TRANSPORT_STD))
    ret       = max(3,   random.gauss(RETURN_MEAN,    RETURN_STD))

    ambulances[amb_idx]["available"] = False
    yield env.timeout(chute + travel + on_scene + transport + ret)
    ambulances[amb_idx]["available"] = True

def call_generator(env, ambulances):
    while True:
        sim_minute = env.now
        rate       = get_call_rate(sim_minute)

        interarrival = random.expovariate(rate)
        yield env.timeout(interarrival)

        demand_idx = random.randint(0, n_demand - 1)
        period     = get_period(env.now % (24 * 60))
        city       = get_city(str(demand_names[demand_idx]))

        amb_idx, travel_time = nearest_available(ambulances, demand_idx, env.now)

        results_log["total_calls"]            += 1
        results_log["calls_by_period"][period] += 1
        results_log["calls_by_city"][city]     += 1

        if amb_idx is None:
            results_log["no_ambulance"] += 1
        else:
            chute_time    = max(0.5, random.gauss(CHUTE_TIME_MEAN, CHUTE_TIME_STD))
            response_time = chute_time + travel_time

            results_log["response_times"].append(response_time)
            results_log["response_by_period"][period].append(response_time)
            results_log["response_by_city"][city].append(response_time)
            results_log["city_period_response"][f"{city}_{period}"].append(response_time)

            if response_time <= 8.0:
                results_log["covered_8"]  += 1
            if response_time <= 12.0:
                results_log["covered_12"] += 1

            env.process(ambulance_call(env, amb_idx, ambulances, demand_idx, env.now))

def run_simulation():
    random.seed(RANDOM_SEED)
    env = simpy.Environment()

    staging_indices = get_staging_indices("midday")
    ambulances = [
        {"staging": idx, "available": True}
        for idx in staging_indices
    ]

    env.process(call_generator(env, ambulances))
    env.run(until=SIM_DAYS * 24 * 60)

# ── 9. Run Simulation ─────────────────────────────────────────
print("Running simulation...")
run_simulation()

total = results_log["total_calls"]
rt    = results_log["response_times"]

# ── 10. Overall Results ───────────────────────────────────────
print(f"\n{'='*50}")
print(f"SIMULATION RESULTS — {SIM_DAYS} days")
print(f"{'='*50}")
print(f"Total calls simulated:        {total}")
print(f"Calls with no ambulance:      {results_log['no_ambulance']} ({results_log['no_ambulance']/total*100:.1f}%)")
print(f"Avg response time:            {np.mean(rt):.1f} min")
print(f"Median response time:         {np.median(rt):.1f} min")
print(f"Worst response time:          {np.max(rt):.1f} min")
print(f"% calls under 8 min:          {results_log['covered_8']/total*100:.1f}%")
print(f"% calls under 12 min:         {results_log['covered_12']/total*100:.1f}%")

# ── 11. Results by Time Period ────────────────────────────────
print(f"\n--- Results by Time Period ---\n")
print(f"{'Period':<12} {'Calls':>8} {'Avg':>8} {'Median':>8} {'<8min':>8} {'<12min':>8}")
print("-" * 55)

for period in ["night", "morning", "midday", "evening", "late"]:
    calls = results_log["calls_by_period"][period]
    times = results_log["response_by_period"][period]
    if times:
        avg = np.mean(times)
        med = np.median(times)
        u8  = sum(1 for t in times if t <= 8.0)  / len(times) * 100
        u12 = sum(1 for t in times if t <= 12.0) / len(times) * 100
        print(f"{period:<12} {calls:>8} {avg:>7.1f} {med:>8.1f} {u8:>7.1f}% {u12:>7.1f}%")

# ── 12. Results by City ───────────────────────────────────────
print(f"\n--- Results by City ---\n")
print(f"{'City':<15} {'Calls':>8} {'Avg':>8} {'Median':>8} {'<8min':>8} {'<12min':>8}")
print("-" * 60)

for city in ["Wise", "Norton", "Big Stone Gap", "Corridor"]:
    calls = results_log["calls_by_city"][city]
    times = results_log["response_by_city"][city]
    if times:
        avg = np.mean(times)
        med = np.median(times)
        u8  = sum(1 for t in times if t <= 8.0)  / len(times) * 100
        u12 = sum(1 for t in times if t <= 12.0) / len(times) * 100
        print(f"{city:<15} {calls:>8} {avg:>7.1f} {med:>8.1f} {u8:>7.1f}% {u12:>7.1f}%")

# ── 13. City x Period Breakdown ───────────────────────────────
print(f"\n--- Average Response Time by City and Period ---\n")
print(f"{'':15} {'night':>8} {'morning':>8} {'midday':>8} {'evening':>8} {'late':>8}")
print("-" * 55)

for city in ["Wise", "Norton", "Big Stone Gap", "Corridor"]:
    row = f"{city:<15}"
    for period in ["night", "morning", "midday", "evening", "late"]:
        key   = f"{city}_{period}"
        times = results_log["city_period_response"][key]
        avg   = np.mean(times) if times else 0.0
        row  += f" {avg:>8.1f}"
    print(row)

# ── 14. Comparison to Historical Data ────────────────────────
print(f"\n--- Comparison to Historical Data ---\n")
print(f"{'Period':<12} {'Historical':>12} {'Simulated':>12} {'Improvement':>12}")
print("-" * 50)

for period in ["night", "morning", "midday", "evening", "late"]:
    times = results_log["response_by_period"][period]
    if times:
        hist = historical_response[period]
        sim  = np.mean(times)
        imp  = hist - sim
        print(f"{period:<12} {hist:>11.1f}m {sim:>11.1f}m {imp:>+11.1f}m")

# ── 15. Outlier Analysis ──────────────────────────────────────
print("\n--- Outlier Analysis ---")
outliers = [t for t in results_log["response_times"] if t > 12.0]
print(f"Calls exceeding 12 minutes: {len(outliers)} ({len(outliers)/total*100:.1f}%)")
print(f"Calls exceeding 20 minutes: {sum(1 for t in results_log['response_times'] if t > 20.0)}")
print(f"Calls exceeding 30 minutes: {sum(1 for t in results_log['response_times'] if t > 30.0)}")