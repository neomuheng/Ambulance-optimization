Ambulance Deployment Optimization — Wise County, VA

UVA Wise Mathematical Modeling Competition, Spring 2026

##Requirements##

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


README.md         — this file

