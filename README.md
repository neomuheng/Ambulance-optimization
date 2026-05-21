
---

# Ambulance Deployment Optimization — Wise County, Virginia

**UVA Wise Mathematical Modeling Competition**

---

## Overview

This project develops an evidence-based ambulance deployment optimization model for Wise County, Virginia, covering the municipalities of Wise, Norton, and Big Stone Gap. The goal is to maximize emergency medical coverage across the county's challenging terrain while respecting real-world constraints like existing station locations and resource limits.

The model combines classical operations research (Maximum Coverage Location Problem) with discrete-event simulation to both prescribe optimal deployments and stress-test them under realistic demand conditions.

---

## Repository Structure

```
Ambulance-optimization/
├── EMS.py                      # Main entry point
├── optimization.py             # MCLP optimization using PuLP
├── simulations.py              # Discrete-event simulation using SimPy
├── visuals.py                  # Coverage maps and result plots
├── dp.py                       # Demand point and station mapping
├── map.py                      # Road network / geographic mapping
├── WRS_1.pdf                   # Wise Rescue Squad dispatch records (set 1)
├── WRS_2.pdf                   # Wise Rescue Squad dispatch records (set 2)
├── chart1_response_time.png    # Response time distribution chart
├── chart2_coverage.png         # Coverage area visualization
├── chart3_call_volume.png      # Call volume analysis
├── chart4_fleet_heatmap.png    # Fleet utilization heatmap
├── chart5_distribution.png     # Demand distribution chart
└── README.md
```

---

## Methodology

**Phase 1 — Demand Estimation**
Real dispatch records from Wise Rescue Squad (`WRS_1.pdf`, `WRS_2.pdf`) were parsed to build a spatial and temporal demand model, capturing where and when calls occur across the county. Demand points and station locations are handled in `dp.py`.

**Phase 2 — MCLP Optimization**
The Maximum Coverage Location Problem is solved in `optimization.py` using PuLP to find ambulance staging locations that maximize population coverage within a target response time. Key parameters:
- Coverage target: 80%
- Travel time adjustment factor: ~0.74 (accounts for lights-and-sirens speeds)
- Existing WRS staging locations retained as fixed constraints

**Phase 3 — Simulation**
`simulations.py` uses SimPy to stress-test the optimized deployment against stochastic call arrival patterns, measuring response time distributions, unit utilization rates, and coverage degradation under high-demand scenarios.

**Phase 4 — Visualization**
`visuals.py` and `map.py` generate coverage maps overlaid on the county road network, along with five output charts covering response times, coverage area, call volume, fleet utilization, and demand distribution.

---

## Output Charts

| File | Description |
|------|-------------|
| `chart1_response_time.png` | Response time distribution across simulated calls |
| `chart2_coverage.png` | Geographic coverage visualization |
| `chart3_call_volume.png` | Call volume by area and time |
| `chart4_fleet_heatmap.png` | Ambulance utilization heatmap |
| `chart5_distribution.png` | Spatial demand distribution |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| PuLP | Linear programming / MCLP solver |
| SimPy | Discrete-event simulation |
| matplotlib | Mapping and visualization |
| OSRM / Docker | Road network routing |

---

## Setup & Usage

```bash
# Clone the repository
git clone https://github.com/neomuheng/Ambulance-optimization

# Install dependencies
pip install pulp simpy matplotlib

# Run the main script
python EMS.py

# Or run individual components
python optimization.py
python simulations.py
python visuals.py
```

> Note: OSRM requires Docker for local road network routing. Large map files are excluded from the repo due to GitHub size limits.

---

## Data Sources

- Wise Rescue Squad dispatch logs (`WRS_1.pdf`, `WRS_2.pdf`)
- Wise County geographic and road network data
- U.S. Census population distribution data

---

> Note: Wise Rescue Squad dispatch logs should be requested through the Wise Sheriff's Office

## How to run the program

pip install osmnx scikit-learn matplotlib numpy requests pulp simpy pdfplumber pandas

##Setup Instructions##

1. Install Docker Desktop

Download from docker.com/get-started

2. Download Virginia Road Network

Download virginia-latest.osm.pbf from:

https://download.geofabrik.de/north-america/us/virginia.html

3. Process OSRM Map Data

Run these commands in your project folder:

docker run -t -v "/your/path:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/virginia-latest.osm.pbf

docker run -t -v "/your/path:/data" osrm/osrm-backend osrm-partition /data/virginia-latest.osrm

docker run -t -v "/your/path:/data" osrm/osrm-backend osrm-customize /data/virginia-latest.osrm

4. Start OSRM Server

docker run -t -p 5000:5000 -v "/your/path:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/virginia-latest.osrm

5. Update File Paths

In each script, update save_dir to your project folder:

save_dir = "C:/your/path/here"

