import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from archive import ROOT, validate_catalog, validate_repository
from documentary import record_version


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data.json').read_text())

    def test_authoritative_repository(self):
        self.assertEqual(validate_repository(), len(self.data['records']))

    def test_incomplete_or_broken_catalog_rejected(self):
        for case in ['empty', 'duplicate', 'field', 'relation', 'regional_reference', 'url']:
            with self.subTest(case=case):
                data = copy.deepcopy(self.data)
                if case == 'empty': data['records'] = []
                if case == 'duplicate': data['records'].append(data['records'][0])
                if case == 'field': del data['records'][0]['title']
                if case == 'relation': data['records'][0]['relations'] = [{'type': 'Modifica', 'id': 'missing'}]
                if case == 'regional_reference': data['regions'][0]['plan_ids'].append('missing')
                if case == 'url': data['records'][0]['url'] = 'http://example.gov/act'
                with self.assertRaises(ValueError): validate_catalog(data)

    def test_retention_allows_updates_and_additions_but_not_losses(self):
        data = copy.deepcopy(self.data)
        data['records'][0]['summary'] += ' Aggiornamento verificato.'
        record = data['records'][0]
        if record.get('documentary_review'):
            # An updated reviewed object must preserve its former evidence.
            record.setdefault('documentary_history', []).append(
                copy.deepcopy(self.data['records'][0]['documentary_review']))
            record['documentary_review']['record_version'] = record_version(record)
        extra = copy.deepcopy(data['records'][0]); extra['id'] = 'new-record'
        data['records'].append(extra)
        self.assertEqual(validate_catalog(data, self.data), len(self.data['records']) + 1)
        data['updatedAt'] = '2000-01-01'
        with self.assertRaisesRegex(ValueError, 'Edizione'): validate_catalog(data, self.data)
        data['updatedAt'] = self.data['updatedAt']
        data['records'] = [r for r in data['records'] if r['id'] != 'uni858']
        with self.assertRaisesRegex(ValueError, 'Schede perse'): validate_catalog(data, self.data)

    def test_distribution_copy_cannot_return(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'dist').mkdir()
            with self.assertRaisesRegex(ValueError, 'dist/'): validate_repository(root)

    def test_normative_history_cannot_be_lost(self):
        data = copy.deepcopy(self.data)
        record = next(r for r in data['records'] if r['history'])
        record['history'] = []
        with self.assertRaisesRegex(ValueError, 'cronologia precedente rimossa'):
            validate_catalog(data, self.data)


if __name__ == '__main__': unittest.main()
