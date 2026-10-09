"""Generate the map and GitHub Pages entry point from the local snapshot."""
import argparse
import json
from pathlib import Path
from src.data_handler import load_occurrences
from src.map_builder import build_map

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write one HTML file instead of the default two')
    args = parser.parse_args()
    records = load_occurrences(ROOT / 'data/occurrences.json')
    metadata = json.loads((ROOT / 'data/provenance.json').read_text(encoding='utf-8'))
    html = build_map(records, metadata)
    outputs = [args.output] if args.output else [ROOT / 'BiomiNO_map.html', ROOT / 'docs/index.html']
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding='utf-8')
        print(f'Built {output}: {len(records):,} records, {len(html.encode()):,} bytes')


if __name__ == '__main__':
    main()
