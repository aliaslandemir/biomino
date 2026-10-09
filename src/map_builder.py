"""Build portable map pages from local assets, without a Python web stack."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_map(records, metadata):
    if metadata['record_count'] != len(records):
        raise ValueError('Snapshot and provenance record counts differ')
    taxa = {taxon['key'] for taxon in metadata['taxa']}
    if any(row['taxon_key'] not in taxa for row in records):
        raise ValueError('Occurrence taxon is missing from provenance')
    datasets = {r['dataset_key']: {key: r.get(key, '') for key in ('dataset', 'citation', 'publisher')} for r in records}
    compact_records = [{k: v for k, v in r.items() if k not in ('dataset', 'citation', 'publisher')} for r in records]
    template = (ROOT / 'web/template.html').read_text(encoding='utf-8')
    assets = {
        '__STYLES__': '\n'.join((ROOT / path).read_text(encoding='utf-8') for path in
                              ['web/vendor/leaflet.css', 'web/vendor/markercluster.css', 'web/app.css']),
        '__LIBRARIES__': '\n'.join((ROOT / path).read_text(encoding='utf-8') for path in
                                 ['web/vendor/leaflet.js', 'web/vendor/markercluster.js']),
        '__APP__': (ROOT / 'web/app.js').read_text(encoding='utf-8'),
        '__DATA__': json.dumps({'records': compact_records, 'metadata': metadata, 'datasets': datasets}, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'),
    }
    for token, value in assets.items():
        template = template.replace(token, value)
    return template
