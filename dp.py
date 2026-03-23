import folium
import os

save_dir = "C:/Users/vipon/Downloads/Ambulance"

# ── Demand Nodes ──────────────────────────────────────────────
wise_nodes = {
    "Downtown Wise":                    (36.9760, -82.5754),
    "Wise County Central High":         (36.9557, -82.5979),
    "Heritage Hall Wise":               (36.9680, -82.5582),
    "UVA Wise Campus":                  (36.9747, -82.5588),
    "Wise County Sheriff Department":   (36.9678, -82.5505),
    "Wise County Animal Hospital":      (36.9778, -82.5698),
    "G&M Plumbing":                     (36.9760, -82.5701),
    "Wise County Technical School":     (36.9830, -82.5687),
    "Lighthouse Family Worship Center": (36.9885, -82.5818),
    "Warrior Wash":                     (36.9855, -82.5891),
    "Hardee's Wise":                    (36.9801, -82.5821),
    "Leonard D Rogers PC":              (36.9811, -82.5787),
    "Lowes Home Improvement":           (36.9736, -82.5894),
    "Wise Municipal Pool":              (36.9731, -82.5757),
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
    "Dollar General Norton":            (36.9307, -82.6472),
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
    "Dog Shop BSG":                      (36.8806, -82.7530),
}

# ── Staging Locations ─────────────────────────────────────────
staging_locations = {
    "Wise Fire Department":      (36.9763, -82.5821),
    "Wise Rescue Squad":         (36.9798, -82.5762),
    "Norton Fire Department":    (36.9355, -82.6285),
    "Norton Community Hospital": (36.9331, -82.6426),
    "BSG Fire Department":       (36.8680, -82.7759),
    "Lonesome Pine Hospital":    (36.8783, -82.7521),
}

# ── Create Map ────────────────────────────────────────────────
# Center on midpoint of service area
m = folium.Map(
    location=[36.9200, -82.6700],
    zoom_start=12,
    tiles="OpenStreetMap"
)

# ── Add Demand Nodes ──────────────────────────────────────────
# Wise — blue
for name, (lat, lon) in wise_nodes.items():
    folium.CircleMarker(
        location=[lat, lon],
        radius=7,
        color="#2c5282",
        fill=True,
        fill_color="#4299e1",
        fill_opacity=0.8,
        tooltip=f"WISE: {name}",
        popup=folium.Popup(f"<b>Wise</b><br>{name}<br>({lat:.4f}, {lon:.4f})", max_width=200)
    ).add_to(m)

# Norton — green
for name, (lat, lon) in norton_nodes.items():
    folium.CircleMarker(
        location=[lat, lon],
        radius=7,
        color="#276749",
        fill=True,
        fill_color="#48bb78",
        fill_opacity=0.8,
        tooltip=f"NORTON: {name}",
        popup=folium.Popup(f"<b>Norton</b><br>{name}<br>({lat:.4f}, {lon:.4f})", max_width=200)
    ).add_to(m)

# Big Stone Gap — orange
for name, (lat, lon) in bsg_nodes.items():
    color = "#c05621" if name == "Wallens Ridge State Prison" else "#c05621"
    fill  = "#fc8181" if name == "Wallens Ridge State Prison" else "#ed8936"
    folium.CircleMarker(
        location=[lat, lon],
        radius=7,
        color=color,
        fill=True,
        fill_color=fill,
        fill_opacity=0.8,
        tooltip=f"BSG: {name}",
        popup=folium.Popup(f"<b>Big Stone Gap</b><br>{name}<br>({lat:.4f}, {lon:.4f})", max_width=200)
    ).add_to(m)

# ── Add Staging Locations ─────────────────────────────────────
for name, (lat, lon) in staging_locations.items():
    folium.Marker(
        location=[lat, lon],
        tooltip=f"STAGING: {name}",
        popup=folium.Popup(f"<b>Staging Location</b><br>{name}", max_width=200),
        icon=folium.Icon(color="red", icon="plus-sign", prefix="glyphicon")
    ).add_to(m)

# ── Add Legend ────────────────────────────────────────────────
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
     background-color: white; padding: 15px; border-radius: 8px;
     border: 2px solid #cccccc; font-family: Arial; font-size: 13px;">
    <b>Map Legend</b><br><br>
    <span style="color:#4299e1;">&#9679;</span> Wise demand node<br>
    <span style="color:#48bb78;">&#9679;</span> Norton demand node<br>
    <span style="color:#ed8936;">&#9679;</span> Big Stone Gap demand node<br>
    <span style="color:#fc8181;">&#9679;</span> Wallens Ridge (exception)<br>
    <span style="color:red;">&#10010;</span> Staging location<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ── Save Map ──────────────────────────────────────────────────
output_path = os.path.join(save_dir, "demand_nodes_map.html")
m.save(output_path)
print(f"Map saved to {output_path}")