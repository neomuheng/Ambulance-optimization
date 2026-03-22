\# Ambulance Deployment Optimization — Wise County, VA

UVA Wise Mathematical Modeling Competition, Spring 2026



\## Project Overview

Dynamic ambulance staging optimization model for Wise, Norton, 

and Big Stone Gap, Virginia. Uses Maximum Coverage Location 

Problem (MCLP) optimization and discrete-event simulation to 

recommend ambulance staging locations by time of day and day of week.



\## Requirements

pip install osmnx scikit-learn matplotlib numpy requests pulp simpy pdfplumber pandas



\## Setup Instructions



\### 1. Install Docker Desktop

Download from docker.com/get-started



\### 2. Download Virginia Road Network

Download virginia-latest.osm.pbf from:

https://download.geofabrik.de/north-america/us/virginia.html



\### 3. Process OSRM Map Data

Run these commands in your project folder:



docker run -t -v "/your/path:/data" osrm/osrm-backend osrm-extract \\

&#x20; -p /opt/car.lua /data/virginia-latest.osm.pbf



docker run -t -v "/your/path:/data" osrm/osrm-backend osrm-partition \\

&#x20; /data/virginia-latest.osrm



docker run -t -v "/your/path:/data" osrm/osrm-backend osrm-customize \\

&#x20; /data/virginia-latest.osrm



\### 4. Start OSRM Server

docker run -t -p 5000:5000 -v "/your/path:/data" osrm/osrm-backend \\

&#x20; osrm-routed --algorithm mld /data/virginia-latest.osrm



\### 5. Update File Paths

In each script, update save\_dir to your project folder:

save\_dir = "C:/your/path/here"



\## Running the Model

Run scripts in order:

1\. python step1.py   — builds travel time matrix

2\. python step2.py   — runs MCLP optimization

3\. python step3.py   — runs simulation

4\. python step4.py   — generates charts



\## File Structure

step1.py          — road network + travel time matrix

step2.py          — MCLP optimization

step3.py          — discrete event simulation

step4.py          — visualizations

EMS.py            — historical data analysis

README.md         — this file

