import os
import logging
from src.data_handler import load_locations_from_csv
from src.map_builder import (
    build_base_map,
    add_clustered_markers,
    add_markers,  # Direct marker addition for debugging
    add_geojson_layer,
    add_search_feature,
    create_geojson_point,
    geojson_feature_to_marker
)

def main():
    # Set up logging for diagnostics.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Define the CSV file path.
    csv_path = os.path.join("src", "biomineral_data.csv")
    try:
        locations_data = load_locations_from_csv(csv_path)
        logging.info(f"Loaded {len(locations_data)} location(s) from {csv_path}")
    except Exception as e:
        logging.exception("Failed to load location data from CSV.")
        return

    # Optional: Add a marker from a GeoJSON feature created from DMS coordinates.
    # Example: Center of Norway (63°59′26″N, 12°18′28″E).
    properties = {
        "name": "Center of Norway",
        "species": "N/A",
        "info_link": "https://example.com/info",
        "color": "black"
    }
    geojson_feature = create_geojson_point("63°59′26″N", "12°18′28″E", properties)
    center_marker = geojson_feature_to_marker(geojson_feature)
    locations_data.append(center_marker)

    # Build the base map.
    base_map = build_base_map(
        location=(60.4720, 8.4689),
        zoom_start=5,
        tile_provider="google",  # Try "google" or "stamen_terrain" if needed.
        add_measure_control=True,
        add_fullscreen_control=True
    )

    # Uncomment one of the following lines:
    # Use clustered markers:
    # final_map = add_clustered_markers(base_map, locations_data)
    # Or, for debugging, add markers directly (bypassing clustering):
    final_map = add_markers(base_map, locations_data)

    # Optionally add a GeoJSON layer if available.
    geojson_path = os.path.join("src", "norway_regions.geojson")
    if os.path.exists(geojson_path):
        final_map = add_geojson_layer(final_map, geojson_path)
        logging.info("GeoJSON layer added.")
    else:
        logging.info("GeoJSON file not found; skipping GeoJSON layer.")

    # Optionally, add a search feature (if implemented).
    # add_search_feature(final_map)

    # Save the final map to HTML.
    output_html = "BiomiNO_map.html"
    try:
        final_map.save(output_html)
        logging.info(f"Map has been created and saved to: {output_html}")
    except Exception as e:
        logging.exception("Failed to save the map.")

if __name__ == "__main__":
    main()
