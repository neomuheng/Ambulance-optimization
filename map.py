import osmnx as ox
import numpy as np
import requests
import os
import json
save_dir = "C:/Users/vipon/Downloads/Ambulance"

#road network
towns = ["Wise, Virginia, USA", "Norton, Virginia, USA", "Big Stone Gap, Virginia, USA"]
G = ox.graph_from_place(towns, network_type="drive")
#staging nodes
staging_location = {
   "Wise Fire Department":      (36.976270551291805, -82.582094692353),
   "Wise Rescue Squad":         (36.97978667962422, -82.57615300824975),
   "Norton Fire Department":    (36.93553208354384, -82.62845162210398),
   "Norton Community Hospital": (36.933097219617814, -82.64256478491696),
   "Bsg Fore Department":       (36.86799465796641, -82.77588067632671),
   "Bsg Resque squade":         (36.86777694481787, -82.77645025299464),
   "Lonesome Pine Hospital":    (36.878320790952195, -82.75211560094169)
}
#demand nodes
wise_nodes = {
    "Downtown Wise":                   (36.9760, -82.5754),
    "Wise County Central High":        (36.9557, -82.5979),
    "Heritage Hall Wise":              (36.9680, -82.5582),
    "UVA Wise Campus":                 (36.9747, -82.5588),
    "Wise County Sheriff Department":  (36.9678, -82.5505),
    "Wise County Animal Hospital":     (36.9778, -82.5698),
    "G&M Plumbing":                    (36.9760, -82.5701),
    "Wise County Technical School":   (36.9830, -82.5687),
    "Lighthouse Family Worship Center": (36.9885, -82.5818),
    "Warrior Wash":                    (36.9855, -82.5891),
    "Hardee's Wise":                   (36.9801, -82.5821),
    "Leonard D Rogers PC":             (36.9811, -82.5787),
    "Lowes Home Improvement":          (36.9736, -82.5894),
    "Wise Municipal Pool":             (36.9731, -82.5757)
}

norton_nodes = {
    "Norton City Center":               (36.9406, -82.6215),
    "Norton Community Hospital":        (36.9333, -82.6393),
    "Walmart Supercenter Norton":       (36.9567, -82.6018),
    "Wrap Norton":                      (36.9473, -82.6084),
    "Ramsey Freewill Baptist":          (36.9376, -82.5942),
    "Fishtales":                        (36.9416, -82.6016),
    "Cananchee Creek":                  (36.9414, -82.6255),
    "Central Free Will Baptist Church": (36.9318, -82.6281),
    "Lincoln Road Coffee Lounge":       (36.9347, -82.6292),
    "CVS Norton":                       (36.9320, -82.6331),
    "Cinema City":                      (36.9369, -82.6202),
    "Jacob Justice":                    (36.9504, -82.6160),
    "Snack Shack":                      (36.9464, -82.6175),
    "Dollar General Norton":            (36.9307, -82.6472)
}

bsg_nodes = {
    "Union High School BSG":             (36.8796, -82.7381),
    "Mountain Empire Community College": (36.8554, -82.7577),
    "Wallens Ridge State Prison":        (36.8415, -82.7866),
    "Department of Veterans Services":   (36.8541, -82.7652),
    "Trinity Methodist Church":          (36.8632, -82.7762),
    "Sunoco Gas Station BSG":            (36.8597, -82.7844),
    "Pizza Plus BSG":                    (36.8722, -82.7792),
    "Food Bank Wise County":             (36.8604, -82.7900),
    "United States Postal Service BSG":  (36.8673, -82.7427),
    "Bobs Market":                       (36.8825, -82.7452),
    "Oak Grove Baptist Church":          (36.8763, -82.7681),
    "1339 Wildcat Rd BSG":               (36.8428, -82.7618),
    "Iron Works Fitness":                (36.8707, -82.7748),
    "Cavalier Motor Works":              (36.8548, -82.7995),
    "BP Gas Station BSG":                (36.8636, -82.7601),
    "The Pastry Cottage":                (36.8597, -82.7572),
    "Lonesome Pine Motorworks":          (36.8664, -82.7388),
    "2241 Carter St BSG":                (36.8672, -82.7639),
    "Dog Shop BSG":                      (36.8806, -82.7530)
}
demand_nodes = {**wise_nodes, **norton_nodes, **bsg_nodes}
#Total demand nodes
print("After deduplication:", len(demand_nodes))

#Travel Time matrix
def get_travel_time(origin_lat, origin_lon, dest_lat, dest_lon):
    url = (f"http://localhost:5000/route/v1/driving/"
           f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}")
    r = requests.get(url, params={"overview": "false"})
    return r.json()["routes"][0]["duration"] / 60

# Remove grid nodes that are too remote (no staging location within 20 min)
filtered_demand_nodes = {}
for name, coords in demand_nodes.items():
    # Keep all hand-picked nodes regardless
    if not name.startswith("grid"):
        filtered_demand_nodes[name] = coords
        continue
    
    # For grid nodes, check if any staging location is within 20 min
    lat, lon = coords
    times = []
    for s_name, (s_lat, s_lon) in staging_location.items():
        t = get_travel_time(s_lat, s_lon, lat, lon)
        times.append(t)
    
    if min(times) <= 12.0:
        filtered_demand_nodes[name] = coords
    else:
        print(f"Removed remote node: {name} (min time: {min(times):.1f} min)")

demand_nodes = filtered_demand_nodes
print(f"Demand nodes after filtering: {len(demand_nodes)}")

staging_list = list(staging_location.items())
demand_list  = list(demand_nodes.items())

travel_matrix = np.zeros((len(demand_list), len(staging_list)))

for i, (d_name, (d_lat, d_lon)) in enumerate(demand_list):
    for j, (s_name, (s_lat, s_lon)) in enumerate(staging_list):
        travel_matrix[i, j] = get_travel_time(s_lat, s_lon, d_lat, d_lon)

print("Travel matrix shape:", travel_matrix.shape)

#Time-of-Day Adjusted Matrices
traffic_multipliers = {
    "night":   0.80,
    "morning": 0.90,
    "midday":  1.00,
    "evening": 1.10,
    "late":    1.00,
}

# ── 9. Day-of-Week Multipliers (from Wise County EMS data) ────
dow_multipliers = {
    "monday":    1.05,  # 4.4 avg calls
    "tuesday":   0.86,  # 3.6 avg calls — lightest
    "wednesday": 1.03,  # 4.3 avg calls
    "thursday":  0.95,  # 4.0 avg calls
    "friday":    1.15,  # 4.8 avg calls — busiest
    "saturday":  1.03,  # 4.3 avg calls
    "sunday":    0.93,  # 3.9 avg calls
}

# ── 10. Build Combined Matrices (7 days × 5 periods = 35) ─────
combined_matrices = {}
for day, dow_mult in dow_multipliers.items():
    for period, tod_mult in traffic_multipliers.items():
        key = f"{day}_{period}"
        combined_matrices[key] = travel_matrix * tod_mult * dow_mult

print(f"Combined matrices created: {len(combined_matrices)} total")

# ── 11. Save Everything ───────────────────────────────────────
np.save(os.path.join(save_dir, "travel_matrix.npy"), travel_matrix)
np.save(os.path.join(save_dir, "staging_list.npy"),
        np.array([name for name, _ in staging_list]))
np.save(os.path.join(save_dir, "demand_list.npy"),
        np.array([name for name, _ in demand_list]))

for key, matrix in combined_matrices.items():
    np.save(os.path.join(save_dir, f"travel_matrix_{key}.npy"), matrix)

print("All files saved to:", save_dir)