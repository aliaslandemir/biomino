import os
from SRC.data_handler import load_locations_from_csv
from SRC.map_builder import (
    build_base_map,
    add_clustered_markers,
    add_geojson_layer,
    add_search_feature
)

def main():
    # Path to your CSV
    csv_path = os.path.join("SRC", "biomineral_data.csv")

    # 1. Load data
    locations_data = load_locations_from_csv(csv_path)
    print(f"Loaded {len(locations_data)} location(s) from {csv_path}")

    # 2. Build the base map
    # Center on Norway (60.4720, 8.4689)
    base_map = build_base_map(
        location=(60.4720, 8.4689),
        zoom_start=5,
        tiles="Stamen Terrain",  # e.g. "Stamen Terrain", "OpenStreetMap", etc.
        add_measure_control=True,
        add_fullscreen_control=True
    )

    # 3. Add markers
    clustered_map = add_clustered_markers(base_map, locations_data)
    
    # 4. Optionally add a GeoJSON layer (uncomment if you have a .geojson file)
    # geojson_path = os.path.join("SRC", "norway_regions.geojson")
    # if os.path.exists(geojson_path):
    #     add_geojson_layer(clustered_map, geojson_path)

    # 5. (Optional) Add a search feature if you have FeatureGroup or GeoJson
    # add_search_feature(clustered_map)

    # 6. Save the final map to HTML
    output_html = "BiomiNO_map.html"
    clustered_map.save(output_html)
    print(f"Map has been created and saved to: {output_html}")


if __name__ == "__main__":
    main()
