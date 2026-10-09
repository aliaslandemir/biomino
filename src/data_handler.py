"""Validate the checked-in occurrence snapshot before publishing it."""
import json
import math
from pathlib import Path

REQUIRED = {'id', 'lat', 'lon', 'species', 'common_name', 'group', 'source', 'license', 'dataset_key'}


def load_occurrences(path):
    records = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(records, list) or not records:
        raise ValueError('Occurrence data must be a non-empty list')
    seen = set()
    for row in records:
        if not isinstance(row, dict) or REQUIRED - row.keys():
            raise ValueError('Occurrence is missing required fields')
        if not str(row['id']).isdigit() or row['id'] in seen:
            raise ValueError(f"Invalid or duplicate occurrence ID: {row['id']}")
        seen.add(row['id'])
        for field, low, high in [('lat', 57, 72), ('lon', 2, 33)]:
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"Invalid {field} for occurrence {row['id']}")
        if row['source'] != f"https://www.gbif.org/occurrence/{row['id']}":
            raise ValueError('Occurrence source does not match its ID')
        if row['license'] not in {
            'http://creativecommons.org/publicdomain/zero/1.0/',
            'https://creativecommons.org/publicdomain/zero/1.0/',
            'http://creativecommons.org/licenses/by/4.0/',
            'https://creativecommons.org/licenses/by/4.0/',
        }:
            raise ValueError('Unsupported data license')
    return records
