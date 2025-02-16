import re
import folium
from folium import plugins
from folium.plugins import MarkerCluster
from typing import List, Dict, Any, Tuple

def build_base_map(
    location: Tuple[float, float] = (60.4720, 8.4689),
    zoom_start: int = 5,
    tile_provider: str = "stamen_terrain",
    add_measure_control: bool = True,
    add_fullscreen_control: bool = True
) -> folium.Map:
    """
    Build a base Folium map with optional controls.
    tile_provider can be "stamen_terrain", "openstreetmap", or "google".
    """
    tile_provider = tile_provider.lower()
    if tile_provider == "google":
        base_map = folium.Map(location=location, zoom_start=zoom_start, tiles=None)
        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
            attr="Map data © Google",
            name="Google Maps",
            overlay=False,
            control=True
        ).add_to(base_map)
    elif tile_provider == "openstreetmap":
        base_map = folium.Map(location=location, zoom_start=zoom_start, tiles="OpenStreetMap")
    else:
        base_map = folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles="Stamen Terrain",
            attr="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL."
        )

    if add_measure_control:
        plugins.MeasureControl(
            primary_length_unit="meters",
            secondary_length_unit="miles",
            primary_area_unit="sqmeters",
            secondary_area_unit="hectares"
        ).add_to(base_map)

    if add_fullscreen_control:
        plugins.Fullscreen().add_to(base_map)

    folium.LayerControl().add_to(base_map)
    return base_map

def map_color(input_color: str) -> str:
    """
    Map a color string to a valid Folium icon color.
    """
    colors = {
        "red": "red", "blue": "blue", "green": "green", "purple": "purple",
        "orange": "orange", "darkred": "darkred", "lightred": "lightred",
        "beige": "beige", "darkblue": "darkblue", "darkgreen": "darkgreen",
        "cadetblue": "cadetblue", "darkpurple": "darkpurple", "white": "white",
        "pink": "pink", "lightblue": "lightblue", "lightgreen": "lightgreen",
        "gray": "gray", "black": "black", "lightgray": "lightgray"
    }
    return colors.get(input_color.lower(), "blue")

def add_clustered_markers(folium_map: folium.Map, locations_data: List[Dict[str, Any]]) -> folium.Map:
    """
    Add markers to the map using MarkerCluster.
    """
    marker_cluster = MarkerCluster().add_to(folium_map)
    for loc in locations_data:
        print(f"Adding marker (cluster): {loc.get('name')} at ({loc['lat']}, {loc['lon']})")
        popup_html = f"""
        <div style="font-size:14px;">
            <strong>{loc.get('name', 'Unknown')}</strong><br>
            <em>Species:</em> {loc.get('species', 'N/A')}<br><br>
            <img src="{loc.get('image_url', '')}" alt="" width="250"
                 onerror="this.style.display='none'"/><br><br>
            <a href="{loc.get('info_link', '#')}" target="_blank">More Info</a>
        </div>
        """
        marker_color = map_color(loc.get("color", "blue"))
        folium.Marker(
            location=(loc["lat"], loc["lon"]),
            popup=popup_html,
            tooltip=f"{loc.get('name', 'Location')} - Click for details",
            icon=folium.Icon(color=marker_color, icon="info-sign"),
            z_index_offset=2000
        ).add_to(marker_cluster)
    return folium_map

def add_markers(folium_map: folium.Map, locations_data: List[Dict[str, Any]]) -> folium.Map:
    """
    Add markers to the map directly (without clustering) for debugging.
    """
    for loc in locations_data:
        print(f"Adding marker (direct): {loc.get('name')} at ({loc['lat']}, {loc['lon']})")
        popup_html = f"""
        <div style="font-size:14px;">
            <strong>{loc.get('name', 'Unknown')}</strong><br>
            <em>Species:</em> {loc.get('species', 'N/A')}<br><br>
            <img src="{loc.get('image_url', '')}" alt="" width="250"
                 onerror="this.style.display='none'"/><br><br>
            <a href="{loc.get('info_link', '#')}" target="_blank">More Info</a>
        </div>
        """
        marker_color = map_color(loc.get("color", "blue"))
        folium.Marker(
            location=(loc["lat"], loc["lon"]),
            popup=popup_html,
            tooltip=f"{loc.get('name', 'Location')} - Click for details",
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(folium_map)
    return folium_map

def add_geojson_layer(folium_map: folium.Map, geojson_path: str) -> folium.Map:
    """
    Add a GeoJSON layer to the map.
    """
    try:
        folium.GeoJson(geojson_path, name="GeoJSON Layer").add_to(folium_map)
    except Exception as e:
        print(f"Error adding GeoJSON layer: {e}")
    return folium_map

def add_search_feature(folium_map: folium.Map) -> None:
    """
    (Optional) Placeholder for adding a search control.
    """
    pass

def dms_to_decimal(dms_str: str) -> float:
    """
    Convert a DMS string (e.g., "63°59′26″N") to decimal degrees.
    """
    pattern = r"(\d+)°\s*(\d+)′\s*(\d+)″\s*([NSEW])"
    match = re.match(pattern, dms_str.strip())
    if not match:
        raise ValueError(f"Invalid DMS coordinate: {dms_str}")
    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction.upper() in ["S", "W"]:
        decimal = -decimal
    return decimal

def create_geojson_point(dms_lat: str, dms_lon: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a GeoJSON point feature from DMS coordinates.
    """
    lat = dms_to_decimal(dms_lat)
    lon = dms_to_decimal(dms_lon)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]  # GeoJSON uses [lon, lat]
        },
        "properties": properties or {}
    }

def geojson_feature_to_marker(feature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a GeoJSON feature (Point) into a marker dict.
    """
    if feature.get("type") != "Feature":
        raise ValueError("GeoJSON feature must be of type 'Feature'.")
    geometry = feature.get("geometry", {})
    if geometry.get("type") != "Point":
        raise ValueError("GeoJSON geometry must be a Point.")
    coordinates = geometry.get("coordinates", [])
    if len(coordinates) < 2:
        raise ValueError("Invalid coordinates in GeoJSON feature.")
    lon, lat = coordinates[0], coordinates[1]
    props = feature.get("properties", {})
    return {
        "name": props.get("name", "Unknown Location"),
        "lat": lat,
        "lon": lon,
        "species": props.get("species", "N/A"),
        "image_url": props.get("image_url", ""),
        "info_link": props.get("info_link", "#"),
        "color": props.get("color", "blue")
    }
