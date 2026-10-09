import copy
import datetime as dt
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from documentary import record_version, validate_review


class DocumentaryTests(unittest.TestCase):
    def setUp(self):
        self.record = {'id': 'sample', 'ref': 'L.R. 1/2020', 'date': '2020-01-01',
                       'status': 'Testo originario identificato', 'documents': [],
                       'url': 'https://www.regione.test.it/atto'}
        self.record['documentary_review'] = {
            'checked_at': '2026-10-08',
            'scope': 'Identità del testo originario', 'outcome': 'partial',
            'legal_state': 'partial', 'limitations': ['Coordinamento non verificato'],
            'pending': [], 'source_urls': [self.record['url']],
            'claims': [{'aspect': 'identity', 'source_url': self.record['url'],
                        'locator': 'Intestazione', 'finding': 'Numero e data riscontrati'}]}
        self.record['documentary_review']['record_version'] = record_version(self.record)
        self.today = dt.date(2026, 10, 8)

    def check(self, record, baseline=None):
        validate_review(record, baseline, self.today)

    def test_partial_review_and_unrelated_execution_dates(self):
        self.check(self.record)
        record = copy.deepcopy(self.record); record['checked'] = '2026-10-09'
        self.check(record, self.record)

    def test_changed_object_requires_new_review(self):
        for field, value in [('status', 'Vigente'), ('url', 'https://www.regione.test.it/new'),
                             ('ref', 'L.R. 2/2020')]:
            record = copy.deepcopy(self.record); record[field] = value
            with self.assertRaisesRegex(ValueError, 'contenuto cambiato'): self.check(record)

    def test_asserted_status_requires_specific_evidence(self):
        legacy = {'id': 'legacy', 'status': 'Da verificare'}
        self.check(legacy)
        changed = {**legacy, 'status': 'Vigente'}
        with self.assertRaisesRegex(ValueError, 'senza evidenza'): self.check(changed, legacy)
        record = copy.deepcopy(self.record); record['status'] = 'Vigente'
        record['documentary_review']['record_version'] = record_version(record)
        with self.assertRaisesRegex(ValueError, 'riscontro specifico'): self.check(record, self.record)
        record = copy.deepcopy(self.record); record['documentary_review']['legal_state'] = 'in_force'
        with self.assertRaisesRegex(ValueError, 'stato giuridico'): self.check(record)

    def test_constitutional_invalidity_is_distinct_and_requires_status_evidence(self):
        record = copy.deepcopy(self.record)
        record['documentary_review']['legal_state'] = 'constitutionally_invalid'
        with self.assertRaisesRegex(ValueError, 'illegittimita costituzionale'):
            self.check(record)
        record['documentary_review']['claims'][0]['aspect'] = 'status'
        self.check(record)
        legacy = {'id': 'legacy', 'status': 'Da verificare'}
        changed = {**legacy, 'status': 'Dichiarata costituzionalmente illegittima'}
        with self.assertRaisesRegex(ValueError, 'senza evidenza'):
            self.check(changed, legacy)

    def test_normative_metadata_and_future_fields_require_reexamination(self):
        for field, value in [
            ('relations', [{'id': 'other', 'type': 'Modifica'}]),
            ('documents', [{'url': self.record['url'], 'label': 'Testo coordinato'}]),
            ('document_note', 'Allegato sostitutivo'),
            ('note', 'Applicazione limitata'),
            ('source_kind', 'Riproduzione istituzionale'),
            ('publication_date', '2020-02-01'),
            ('effective_date', '2020-02-16'),
            ('future_normative_field', {'scope': 'new'}),
        ]:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.record)
                changed[field] = value
                self.assertNotEqual(record_version(changed), record_version(self.record))
                with self.assertRaisesRegex(ValueError, 'contenuto cambiato'):
                    self.check(changed, self.record)

    def test_changed_document_label_is_not_hidden_by_unchanged_url(self):
        record = copy.deepcopy(self.record)
        record['documents'] = [{'url': self.record['url'], 'label': 'Originario'}]
        record['documentary_review']['record_version'] = record_version(record)
        changed = copy.deepcopy(record)
        changed['documents'][0]['label'] = 'Coordinato'
        with self.assertRaisesRegex(ValueError, 'contenuto cambiato'):
            self.check(changed, record)

    def test_reserved_review_source_key_cannot_hide_record_metadata(self):
        for value in [[], ['https://www.regione.test.it/metadata']]:
            changed = copy.deepcopy(self.record)
            changed['review_source_urls'] = value
            with self.assertRaisesRegex(ValueError, 'chiave riservata'):
                record_version(changed)
            with self.assertRaisesRegex(ValueError, 'chiave riservata'):
                self.check(changed, self.record)
            del changed['documentary_review']
            with self.assertRaisesRegex(ValueError, 'chiave riservata'):
                self.check(changed)

    def test_execution_and_evidence_history_do_not_change_object_version(self):
        record = copy.deepcopy(self.record)
        record['history'] = [{'date': '2026-10-08', 'text': 'Controllo tecnico'}]
        record['documentary_history'] = [copy.deepcopy(record['documentary_review'])]
        self.assertEqual(record_version(record), record_version(self.record))

    def test_changed_review_sources_require_new_version_and_preserve_evidence(self):
        record = copy.deepcopy(self.record)
        review = record['documentary_review']
        new_source = 'https://www.regione.test.it/nuova-fonte'
        review['source_urls'] = [new_source]
        review['claims'][0]['source_url'] = new_source
        record['documentary_history'] = [copy.deepcopy(self.record['documentary_review'])]
        with self.assertRaisesRegex(ValueError, 'contenuto cambiato'):
            self.check(record, self.record)
        review['record_version'] = record_version(record)
        self.assertNotEqual(review['record_version'], self.record['documentary_review']['record_version'])
        self.check(record, self.record)
        review['source_urls'].append(self.record['url'])
        review['record_version'] = record_version(record)
        version = record_version(record)
        review['source_urls'].reverse()
        self.assertEqual(record_version(record), version)
        self.check(record, self.record)

    def test_incomplete_future_or_unlinked_evidence_rejected(self):
        for field, value in [('checked_at', '2026-10-09'), ('source_urls', []),
                             ('claims', []), ('limitations', []), ('checked_at', '2019-01-01')]:
            record = copy.deepcopy(self.record); record['documentary_review'][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError): self.check(record)
        record = copy.deepcopy(self.record)
        record['documentary_review']['claims'][0]['source_url'] = 'https://unlinked.test/act'
        with self.assertRaisesRegex(ValueError, 'associata'): self.check(record)

    def test_previous_evidence_must_survive_and_legacy_remains_usable(self):
        self.check({'id': 'legacy', 'status': 'Vigente'})
        record = copy.deepcopy(self.record); record['status'] = 'Testo originario verificato'
        record['documentary_review']['record_version'] = record_version(record)
        with self.assertRaisesRegex(ValueError, 'precedente non conservata'): self.check(record, self.record)
        record['documentary_history'] = [copy.deepcopy(self.record['documentary_review'])]
        self.check(record, self.record)
        del record['documentary_review']
        with self.assertRaises(ValueError): self.check(record, self.record)


if __name__ == '__main__': unittest.main()
