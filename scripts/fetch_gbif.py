"""Refresh a bounded, spatially thinned GBIF occurrence snapshot."""
import argparse
from datetime import date
import json
from itertools import zip_longest
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.gbif.org/v1'
TAXA = [
    ('Mytilus edulis', 'Blue mussel', 'Bivalves', '#277a78'),
    ('Magallana gigas', 'Pacific oyster', 'Bivalves', '#277a78'),
    ('Cerastoderma edule', 'Common cockle', 'Bivalves', '#277a78'),
    ('Pecten maximus', 'King scallop', 'Bivalves', '#277a78'),
    ('Desmophyllum pertusum', 'Cold-water coral', 'Corals', '#dd765d'),
    ('Strongylocentrotus droebachiensis', 'Green sea urchin', 'Sea urchins', '#8572b3'),
    ('Amphibalanus improvisus', 'Bay barnacle', 'Barnacles', '#c69534'),
    ('Lithothamnion glaciale', 'Coralline red alga', 'Coralline algae', '#ba6288'),
]
LICENSES = {'http://creativecommons.org/publicdomain/zero/1.0/',
            'http://creativecommons.org/licenses/by/4.0/',
            'https://creativecommons.org/publicdomain/zero/1.0/',
            'https://creativecommons.org/licenses/by/4.0/'}


def get(path, **params):
    url = f'{API}/{path}' + ('?' + urlencode(params) if params else '')
    for attempt in range(5):
        time.sleep(0.3)
        try:
            with urlopen(Request(url, headers={'User-Agent': 'BiomiNO/1.0 (public occurrence explorer)'}), timeout=45) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
            retry_after = error.headers.get('Retry-After', '')
            delay = int(retry_after) if retry_after.isdigit() else 10 * (attempt + 1)
            time.sleep(min(max(delay, 1), 60))
        except OSError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def fetch_taxon(taxon):
    scientific, common, group, color = taxon
    match = get('species/match', name=scientific, strict='true')
    if match.get('matchType') == 'NONE' or match.get('rank') != 'SPECIES' or match.get('confidence', 0) < 95:
        raise ValueError(f'No confident species match for {scientific}: {match}')
    key = match.get('acceptedUsageKey', match['usageKey'])
    accepted = get(f'species/{key}')
    query = dict(taxonKey=key, country='NO', hasCoordinate='true', hasGeospatialIssue='false',
                 occurrenceStatus='PRESENT', decimalLatitude='57,72', decimalLongitude='2,33', limit=180)
    total = get('occurrence/search', **{**query, 'limit': 0})['count']
    bands = []
    # Round-robin latitude bands improve coastal coverage within the same 900-row budget.
    for south in (57, 60, 63, 66, 69):
        page = get('occurrence/search', **{**query, 'decimalLatitude': f'{south},{south+3}', 'limit': 180}, offset=0)
        bands.append(page['results'])
    candidates = [row for batch in zip_longest(*bands) for row in batch if row is not None]
    selected, cells, ids = [], set(), set()
    rejected = {'license': 0, 'uncertainty': 0, 'duplicate_or_cell': 0, 'coordinates': 0}
    inspected = 0
    for row in candidates:
        inspected += 1
        license_url = row.get('license', '').removesuffix('legalcode')
        if license_url not in LICENSES:
            rejected['license'] += 1
            continue
        uncertainty = row.get('coordinateUncertaintyInMeters')
        if uncertainty is not None and (uncertainty < 0 or uncertainty > 10000):
            rejected['uncertainty'] += 1
            continue
        lat, lon = row.get('decimalLatitude'), row.get('decimalLongitude')
        if lat is None or lon is None or not (57 <= lat <= 72 and 2 <= lon <= 33):
            rejected['coordinates'] += 1
            continue
        cell = (round(lat * 5), round(lon * 5))
        if row['key'] in ids or cell in cells:
            rejected['duplicate_or_cell'] += 1
            continue
        cells.add(cell)
        ids.add(row['key'])
        selected.append({
            'id': str(row['key']), 'lat': lat, 'lon': lon, 'taxon_key': key,
            'species': accepted.get('canonicalName', scientific), 'common_name': common, 'group': group,
            'locality': row.get('locality') or row.get('municipality') or row.get('stateProvince') or 'Norwegian waters',
            'date': row.get('eventDate', ''), 'year': row.get('year'),
            'basis': row.get('basisOfRecord', 'UNKNOWN'), 'uncertainty_m': uncertainty,
            'dataset_key': row.get('datasetKey', ''), 'dataset': row.get('datasetName', 'GBIF dataset'),
            'publisher': row.get('publishingOrgKey', ''), 'recorded_by': row.get('recordedBy', ''),
            'license': license_url, 'source': f"https://www.gbif.org/occurrence/{row['key']}",
            'issues': row.get('issues', []),
        })
        if len(selected) == 150:
            break
    print(f'{scientific}: {len(selected)} retained / {inspected} inspected / {total} matching')
    return selected, dict(name=accepted.get('canonicalName', scientific), query_name=scientific,
                          common_name=common, group=group, color=color, key=key,
                          matching_records=total, fetched=len(candidates), inspected=inspected, retained=len(selected),
                          rejected_before_cap=rejected, query=query)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retrieved', default=date.today().isoformat(), help='Snapshot date (YYYY-MM-DD)')
    args = parser.parse_args()
    date.fromisoformat(args.retrieved)
    results = [fetch_taxon(taxon) for taxon in TAXA]
    records = sorted([r for rows, _ in results for r in rows], key=lambda r: (r['species'], r['id']))
    if not records:
        raise RuntimeError('No records returned; existing snapshot was not replaced')
    dataset_keys = sorted({r['dataset_key'] for r in records})
    datasets = [get(f'dataset/{key}') for key in dataset_keys]
    dataset_lookup = {d['key']: d for d in datasets}
    for record in records:
        dataset = dataset_lookup[record['dataset_key']]
        record['dataset'] = dataset['title']
        record['citation'] = dataset.get('citation', {}).get('text', '')
    metadata = dict(retrieved=args.retrieved, source='GBIF occurrence API', api=API,
                    bounds=[57, 2, 72, 33], cell_degrees=0.2, max_per_species=150,
                    max_candidates_per_species=900, latitude_bands=[[s, s+3] for s in (57, 60, 63, 66, 69)],
                    candidates_per_band=180, candidate_order='round-robin latitude bands; API order within each band', taxa=[meta for _, meta in results],
                    record_count=len(records), licenses=sorted({r['license'] for r in records}))
    # All requests must succeed before replacing the checked-in snapshot.
    (ROOT / 'data/occurrences.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'data/provenance.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
