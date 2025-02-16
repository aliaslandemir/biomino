import folium
from folium import plugins
from folium.plugins import MarkerCluster

def build_base_map(
    location=(60.4720, 8.4689),
    zoom_start=5,
    tiles="OpenStreetMap",
    add_measure_control=True,
    add_fullscreen_control=True
):
    """
    Create a Folium base map with optional measure and fullscreen controls.
    
    Args:
        location (tuple): latitude, longitude to center the map
        zoom_start (int): initial zoom level
        tiles (str): map tile style, e.g., "OpenStreetMap", "Stamen Terrain", etc.
        add_measure_control (bool): whether to add the measure plugin
        add_fullscreen_control (bool): whether to add fullscreen plugin
        
    Returns:
        folium.Map object
    """
    # Create the folium map
    base_map = folium.Map(location=location, zoom_start=zoom_start, tiles=tiles)

    # Add measure control (distance & area)
    if add_measure_control:
        folium.plugins.MeasureControl(
            primary_length_unit='meters',
            secondary_length_unit='miles',
            primary_area_unit='sqmeters',
            secondary_area_unit='hectares'
        ).add_to(base_map)

    # Add a fullscreen toggle option
    if add_fullscreen_control:
        folium.plugins.Fullscreen().add_to(base_map)

    return base_map


def add_clustered_markers(folium_map, locations_data):
    """
    Adds clustered markers to the folium_map.
    Each marker will have a popup containing information about species,
    images, and links.
    
    locations_data: list of dicts, e.g.:
    [
      {
        "name": "Oslo Fjord",
        "lat": 59.9139,
        "lon": 10.7522,
        "species": "Blue Mussel",
        "image_url": "https://example.com/blue_mussel.jpg",
        "info_link": "https://en.wikipedia.org/wiki/Mytilus_edulis",
        "color": "green"
      }, ...
    ]
    """
    # Initialize a MarkerCluster group
    marker_cluster = MarkerCluster().add_to(folium_map)

    for loc in locations_data:
        # Construct a fancy HTML popup
        popup_html = f"""
        <div style="font-size:14px;">
            <strong>{loc.get('name', 'Unknown Location')}</strong><br>
            <em>Species:</em> {loc.get('species', 'N/A')}<br><br>
            <img src="{loc.get('image_url', '')}" alt="species image" width="250" 
                 onerror="this.style.display='none'"/><br><br>
            <a href="{loc.get('info_link', '#')}" target="_blank">More Info</a>
        </div>
        """

        # Marker color logic (optional)
        # fallback to 'blue' if not provided
        marker_color = loc.get('color', 'blue')

        folium.Marker(
            location=(loc['lat'], loc['lon']),
            popup=popup_html,
            tooltip=f"{loc['name']} - Click for details",
            icon=folium.Icon(color=marker_color, icon='info-sign')
        ).add_to(marker_cluster)

    return folium_map


def add_geojson_layer(folium_map, geojson_path):
    """
    (Optional) Adds a GeoJSON layer to the map, e.g. for region boundaries,
    protected areas, etc.
    """
    folium.GeoJson(
        geojson_path,
        name='GeoJSON Layer'
    ).add_to(folium_map)
    return folium_map


def add_search_feature(folium_map):
    """
    (Optional) Adds a Leaflet Search feature that allows searching markers by name.
    This uses the 'Search' plugin in folium.plugins.
    """
    # We must collect all markers' lat, lon, and name to feed into the search plugin
    # Instead of building a separate layer, we'll note you can use folium.plugins.Search
    # only if there's a GeoJson or FeatureGroup with identifiable features.

    # For demonstration, let's assume we have a feature group of markers:
    # In practice, we can add markers to a FeatureGroup instead of a cluster
    # for direct search. We'll outline the structure:

    # from folium.plugins import Search
    # 
    # search = Search(
    #     layer=some_feature_group,  # FeatureGroup or GeoJson
    #     geom_type='Point',
    #     placeholder='Search location',
    #     collapsed=False
    # ).add_to(folium_map)

    # Since we used MarkerCluster, we’ll just show the concept:
    pass
