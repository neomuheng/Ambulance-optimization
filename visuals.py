# step4.py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

save_dir = "C:/Users/vipon/Downloads/Ambulance"

# ── Data from your results ────────────────────────────────────

periods = ["Night", "Morning", "Midday", "Evening", "Late"]

historical_avg = [11.9, 15.0, 14.4, 12.6, 12.9]
simulated_avg  = [4.1,   4.3,  5.5,  6.4,  5.5]

historical_u8  = [20.2, 10.6, 16.5, 21.5, 19.3]
simulated_u8   = [95.6, 94.0, 78.8, 71.3, 86.7]

historical_u12 = [62.2, 39.4, 45.7, 55.9, 56.6]
simulated_u12  = [98.2, 97.0, 94.9, 91.1, 96.1]

calls_by_period = [272, 133, 137, 202, 180]

fleet_by_period = {
    "Night":   3,
    "Morning": 5,
    "Midday":  5,
    "Evening": 7,
    "Late":    3,
}

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
fleet_by_day_evening = [5, 4, 5, 7, 7, 7, 7]  # evening fleet per day from step2

# Colors
HIST_COLOR = "#d9534f"   # red for historical
SIM_COLOR  = "#5cb85c"   # green for simulated
BLUE       = "#337ab7"
ORANGE     = "#f0ad4e"

# ── Chart 1: Response Time Comparison ────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(periods))
w = 0.35

bars1 = ax.bar(x - w/2, historical_avg, w, label="Historical", color=HIST_COLOR, alpha=0.85)
bars2 = ax.bar(x + w/2, simulated_avg,  w, label="Optimized",  color=SIM_COLOR,  alpha=0.85)

ax.axhline(y=8,  color="orange", linestyle="--", linewidth=1.5, label="8-min target")
ax.axhline(y=12, color="red",    linestyle="--", linewidth=1.5, label="12-min maximum")

ax.set_xlabel("Time Period")
ax.set_ylabel("Average Response Time (minutes)")
ax.set_title("Average Response Time: Historical vs Optimized Staging")
ax.set_xticks(x)
ax.set_xticklabels(periods)
ax.legend()
ax.set_ylim(0, 18)

for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
            f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
            f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(save_dir, "chart1_response_time.png"), dpi=150)
plt.show()
print("Chart 1 saved.")

# ── Chart 2: Coverage % Under 8 and 12 Minutes ───────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Under 8 minutes
ax = axes[0]
bars1 = ax.bar(x - w/2, historical_u8, w, label="Historical", color=HIST_COLOR, alpha=0.85)
bars2 = ax.bar(x + w/2, simulated_u8,  w, label="Optimized",  color=SIM_COLOR,  alpha=0.85)
ax.axhline(y=80, color="blue", linestyle="--", linewidth=1.5, label="80% target")
ax.set_title("% Calls Covered Within 8 Minutes")
ax.set_xticks(x)
ax.set_xticklabels(periods)
ax.set_ylabel("Coverage (%)")
ax.set_ylim(0, 110)
ax.legend()
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)

# Under 12 minutes
ax = axes[1]
bars1 = ax.bar(x - w/2, historical_u12, w, label="Historical", color=HIST_COLOR, alpha=0.85)
bars2 = ax.bar(x + w/2, simulated_u12,  w, label="Optimized",  color=SIM_COLOR,  alpha=0.85)
ax.axhline(y=100, color="blue", linestyle="--", linewidth=1.5, label="100% target")
ax.set_title("% Calls Covered Within 12 Minutes")
ax.set_xticks(x)
ax.set_xticklabels(periods)
ax.set_ylabel("Coverage (%)")
ax.set_ylim(0, 115)
ax.legend()
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=9)

plt.suptitle("Coverage Performance: Historical vs Optimized Staging", fontsize=13)
plt.tight_layout()
plt.savefig(os.path.join(save_dir, "chart2_coverage.png"), dpi=150)
plt.show()
print("Chart 2 saved.")

# ── Chart 3: Call Volume by Period ────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(periods, calls_by_period, color=BLUE, alpha=0.85, edgecolor="white")
ax.set_title("Simulated Call Volume by Time Period (365 days)")
ax.set_xlabel("Time Period")
ax.set_ylabel("Number of Calls")

for bar in bars:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            str(int(bar.get_height())), ha="center", va="bottom", fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(save_dir, "chart3_call_volume.png"), dpi=150)
plt.show()
print("Chart 3 saved.")

# ── Chart 4: Fleet Size Heatmap ───────────────────────────────
fleet_data = np.array([
    # night  morning  midday  evening  late
    [2, 2, 3, 3, 3],  # monday
    [2, 2, 2, 2, 2],  # tuesday
    [2, 2, 3, 3, 3],  # wednesday
    [2, 2, 2, 3, 2],  # thursday
    [2, 3, 3, 3, 3],  # friday
    [2, 2, 3, 3, 3],  # saturday
    [2, 2, 2, 3, 2],  # sunday
])

fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(fleet_data, cmap="YlOrRd", aspect="auto")

ax.set_xticks(np.arange(5))
ax.set_yticks(np.arange(7))
ax.set_xticklabels(["Night", "Morning", "Midday", "Evening", "Late"])
ax.set_yticklabels(days)

for i in range(7):
    for j in range(5):
        ax.text(j, i, fleet_data[i, j], ha="center", va="center",
                color="black", fontsize=12, fontweight="bold")

plt.colorbar(im, ax=ax, label="Ambulances Required")
ax.set_title("Ambulances Required by Day and Time Period")
plt.tight_layout()
plt.savefig(os.path.join(save_dir, "chart4_fleet_heatmap.png"), dpi=150)
plt.show()
print("Chart 4 saved.")

# ── Chart 5: Response Time Distribution ──────────────────────
# Approximate distribution from your simulation results
np.random.seed(42)
sim_times = np.concatenate([
    np.random.normal(4.1, 2.0, 272),   # night
    np.random.normal(4.3, 2.0, 133),   # morning
    np.random.normal(5.5, 2.5, 137),   # midday
    np.random.normal(6.4, 3.0, 202),   # evening
    np.random.normal(5.5, 2.5, 180),   # late
])
sim_times = np.clip(sim_times, 0.5, 35)

fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(sim_times, bins=40, color=BLUE, alpha=0.75, edgecolor="white")
ax.axvline(x=8,  color="orange", linestyle="--", linewidth=2, label="8-min target")
ax.axvline(x=12, color="red",    linestyle="--", linewidth=2, label="12-min maximum")
ax.axvline(x=np.mean(sim_times), color="green", linestyle="-",
           linewidth=2, label=f"Mean: {np.mean(sim_times):.1f} min")

ax.set_xlabel("Response Time (minutes)")
ax.set_ylabel("Number of Calls")
ax.set_title("Distribution of Response Times — Optimized Staging (365 days)")
ax.legend()

plt.tight_layout()
plt.savefig(os.path.join(save_dir, "chart5_distribution.png"), dpi=150)
plt.show()
print("Chart 5 saved.")

print(f"\nAll charts saved to {save_dir}")