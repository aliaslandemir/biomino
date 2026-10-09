"""Data integrity and portable build checks. Run with unittest discovery."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from src.data_handler import load_occurrences
from src.map_builder import ROOT, build_map


class MapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_occurrences(ROOT / 'data/occurrences.json')
        cls.metadata = json.loads((ROOT / 'data/provenance.json').read_text())

    def validate(self, records):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.json'
            path.write_text(json.dumps(records))
            return load_occurrences(path)

    def test_snapshot_matches_provenance_and_sampling(self):
        self.assertEqual(len(self.records), self.metadata['record_count'])
        self.assertEqual(len({r['id'] for r in self.records}), len(self.records))
        for taxon in self.metadata['taxa']:
            rows = [r for r in self.records if r['taxon_key'] == taxon['key']]
            self.assertEqual(len(rows), taxon['retained'])
            self.assertLessEqual(len(rows), 150)
            bins = {(round(r['lat']*5), round(r['lon']*5)) for r in rows}
            self.assertEqual(len(rows), len(bins))
        for row in self.records:
            self.assertTrue(row['dataset_key'])
            self.assertTrue(row['citation'])
            self.assertTrue(row['uncertainty_m'] is None or 0 <= row['uncertainty_m'] <= 10000)

    def test_rejects_invalid_coordinates_and_duplicate_ids(self):
        for value in (float('nan'), float('inf'), 90, '60', True):
            rows = copy.deepcopy(self.records[:1]); rows[0]['lat'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): self.validate(rows)
        with self.assertRaises(ValueError): self.validate([self.records[0],self.records[0]])

    def test_rejects_missing_fields_and_untrusted_source(self):
        row = copy.deepcopy(self.records[0]); del row['species']
        with self.assertRaises(ValueError): self.validate([row])
        row = copy.deepcopy(self.records[0]); row['source'] = 'javascript:alert(1)'
        with self.assertRaises(ValueError): self.validate([row])
        row = copy.deepcopy(self.records[0]); row['license'] = 'all rights reserved'
        with self.assertRaises(ValueError): self.validate([row])

    def test_inline_data_cannot_close_script(self):
        records = copy.deepcopy(self.records)
        records[0]['locality'] = '</script><script>alert(1)</script>'
        html = build_map(records, self.metadata)
        self.assertNotIn('</script><script>alert(1)</script>', html)
        self.assertIn('\\u003c/script>', html)

    def test_build_is_deterministic_and_self_contained(self):
        html = build_map(self.records, self.metadata)
        self.assertEqual(html, build_map(self.records, self.metadata))
        self.assertNotIn('<script src=', html)
        self.assertNotIn('__DATA__', html)
        self.assertLess(len(html.encode()), 1000000)
        with self.assertRaises(ValueError): build_map(self.records[:-1], self.metadata)


if __name__ == '__main__':
    unittest.main()
