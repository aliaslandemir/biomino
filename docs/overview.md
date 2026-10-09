# Data and map notes

The map is an occurrence explorer for selected marine species with mineralized structures. It does not run a classifier, detect organisms from images, estimate abundance or predict suitable habitat.

## Snapshot selection

`scripts/fetch_gbif.py` queries the GBIF species API to resolve accepted species keys, then the occurrence API with:

- Country `NO`, latitude 57–72° N, longitude 2–33° E.
- Present occurrences with coordinates and `hasGeospatialIssue=false`.
- Five latitude bands: 57–60, 60–63, 63–66, 66–69 and 69–72° N.
- The first 180 API results in each band, up to 900 candidate records per species. Bands share inclusive boundaries; duplicate IDs are removed.
- Candidate lists interleaved across bands, then one record per species per rounded 0.2° latitude/longitude bin, capped at 150 per species.
- CC0 or CC BY 4.0 licenses. Known coordinate uncertainty above 10,000 m is excluded. Unknown uncertainty is retained.

API order is unspecified and can change. The checked-in JSON is the reproducible input to the map; refreshing it produces a new snapshot. Latitude bands improve coverage within the candidate budget but do not make the sample representative. Coordinate bins are not equal in area. The 0.5° grid view is a separate aggregation of the filtered records.

`data/provenance.json` contains the retrieval date, species keys, query parameters, latitude bands, candidate counts, retained counts and rejection counts. `data/occurrences.json` retains occurrence IDs, coordinates, dates, record type, uncertainty, recorder, dataset citation, source links, licenses and GBIF quality flags. Taxonomic names use GBIF's accepted name at retrieval; older sources may use *Lophelia pertusa* for the cold-water coral or *Crassostrea gigas* for Pacific oyster.

Each record links to its occurrence and dataset page. Citations are obtained from the GBIF dataset API. These are API search results, not a GBIF download with a single download DOI. For research requiring a complete or citable extract, request a GBIF occurrence download and use its assigned DOI.

## Interpretation

Records combine citizen observations, specimen collections and surveys across different years. Reported coordinates may describe collection sites, not the exact position of an organism. Identification and occurrence status are supplied by publishers. GBIF geospatial checks do not verify biological identification. Other flags are displayed in popups and included in GeoJSON exports.

Year filters exclude undated records. Uncertainty filters exclude records whose uncertainty is unknown. Group counts in the filter panel describe the full snapshot; the matching-record count reflects the active filters. Export includes all matching records, including those outside the current viewport. Shared links retain filters and visualization mode, but not the map position or basemap choice.

The old hand-entered examples are preserved in `legacy-example-locations.csv` for reference. They lack occurrence citations and are not used in the current map.

## Sources

- [GBIF occurrence API](https://techdocs.gbif.org/en/openapi/v1/occurrence)
- [GBIF species API](https://techdocs.gbif.org/en/openapi/v1/species)
- [GBIF dataset API](https://techdocs.gbif.org/en/openapi/v1/registry)
- [Institute of Marine Research coral reef WFS](https://data.norge.no/nb/data-services/37f0a484-2ab6-3d6b-918b-5adc69d34a1f/korallrev-wfs-hi): further research source; not included as a layer.
- [OpenStreetMap attribution and license](https://www.openstreetmap.org/copyright)

## Build

The Python builder reads local JSON and embeds the app, Leaflet and marker clustering assets into two identical HTML files. Dataset credits are stored once per dataset in the embedded payload and restored when the app starts. Marker objects and search strings are cached; popups are built on demand. Grid geometry uses Leaflet's canvas renderer. Filtering replaces the marker set in one batch, without a pending asynchronous clustering queue.

Basemap tiles are fetched from OpenStreetMap. The muted option applies a CSS color filter to the same tiles. The tile service requires network access and has its own usage policy. Script assets and records do not need network access. The map shows a notice after repeated tile failures. For high traffic, configure a tile provider suitable for your usage rather than relying on community tile servers.
