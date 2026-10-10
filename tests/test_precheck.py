import copy
import datetime as dt
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import precheck as p

NOW = dt.datetime(2026, 10, 10, 15, tzinfo=dt.timezone.utc)
URL = 'https://www.normattiva.it/document'
HOSTS = {'www.normattiva.it'}


class Response(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'application/pdf', 'ETag': 'v1'}

    def geturl(self):
        return URL


class PrecheckTests(unittest.TestCase):
    def test_complete_pdf_and_variation(self):
        first = p.check(URL, {}, HOSTS, NOW, lambda *a, **k: Response(b'%PDF-1.7 test'))
        self.assertTrue(first['body_complete'])
        self.assertEqual(first['identity_basis'], 'PDF signature only')
        self.assertEqual(first['semantic_verification'], 'not_performed_by_access_check')
        second = p.check(URL, first, HOSTS, NOW, lambda *a, **k: Response(b'%PDF-1.7 changed'))
        self.assertEqual(second['variation'], 'different')
        self.assertEqual(second['previous_observation']['sha256'], first['sha256'])

    def test_prefix_cannot_prove_entire_document_unchanged(self):
        result = p.check(URL, {}, HOSTS, NOW, lambda *a, **k: Response(b'%PDF-' + b'x' * p.MAX_BYTES))
        self.assertFalse(result['body_complete'])
        self.assertNotIn('sha256', result)
        self.assertEqual(result['technical_state'], 'partial_pdf')
        self.assertEqual(result['comparison_scope'], 'prefix_only')

    def test_http_timeout_and_challenge(self):
        for error in [TimeoutError('timeout'), urllib.error.HTTPError(URL, 503, 'unavailable', {}, None)]:
            def fail(*a, **k):
                raise error
            self.assertEqual(p.check(URL, {}, HOSTS, NOW, fail)['technical_state'], 'needs_attention')
        result = p.check(URL, {}, HOSTS, NOW, lambda *a, **k: Response(b'<title>Just a moment</title>captcha'))
        self.assertFalse(p.usable(result))

    def test_redirect_and_unapproved_hosts_are_blocked(self):
        for url in ['http://www.normattiva.it/a', 'https://evil.test/a', 'https://www.normattiva.it:80/a', 'https://user@www.normattiva.it/a']:
            self.assertFalse(p.valid_url(url, HOSTS))
        with self.assertRaises(ValueError):
            p.SafeRedirect(HOSTS).redirect_request(urllib.request.Request(URL), None, 302, '', {}, 'https://evil.test/a')

    def test_conditional_304_retains_observation(self):
        old = {'url': URL, 'sha256': 'abc', 'body_complete': True, 'http_status': 200, 'etag': 'v1'}
        def not_modified(request, **kwargs):
            self.assertEqual(request.get_header('If-none-match'), 'v1')
            raise urllib.error.HTTPError(URL, 304, '', {}, None)
        result = p.check(URL, old, HOSTS, NOW, not_modified)
        self.assertEqual(result['sha256'], 'abc')
        self.assertEqual(result['revalidation_http_status'], 304)

    def test_ttl_and_future_receipts(self):
        receipt = {'checked_at': NOW.isoformat(), 'http_status': 200, 'sha256': 'abc'}
        self.assertFalse(p.due(receipt, NOW + dt.timedelta(days=6)))
        self.assertTrue(p.due(receipt, NOW + dt.timedelta(days=7)))
        self.assertTrue(p.due(receipt, NOW - dt.timedelta(seconds=1)))
        receipt['http_status'] = 503
        self.assertTrue(p.due(receipt, NOW + dt.timedelta(days=1)))

    def test_budget_reuse_invalidation_and_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = p.load(p.ROOT / p.PROGRESS)
            for path in [p.PROGRESS, p.SEED, Path(original['residual_queue']), Path('data.json'), Path('scripts/precheck-hosts.json')]:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes((p.ROOT / path).read_bytes())
            calls = []
            def fetch(url, old, hosts, now):
                calls.append(url)
                return dict(url=url, checked_at=now.isoformat(), http_status=200, sha256='abc', body_complete=True)
            result = p.prepare(root, NOW, 3, 2, fetch, lambda _: None)
            self.assertLessEqual(len(calls), 2)
            self.assertEqual(len(calls), len(set(calls)))
            self.assertEqual(len(result['technical_precheck']['selected']), 3)
            stripped = copy.deepcopy(result)
            stripped.pop('technical_precheck')
            self.assertEqual(stripped, original)
            self.assertTrue(all(t['requires_substantive_review'] for t in result['technical_precheck']['normative_queue']))
            (root / p.PROGRESS).write_text(json.dumps(result), encoding='utf8')
            old_calls = set(calls)
            calls.clear()
            second = p.prepare(root, NOW, 3, 2, fetch, lambda _: None)
            self.assertFalse(old_calls & set(calls))
            self.assertEqual((root / 'data.json').read_bytes(), (p.ROOT / 'data.json').read_bytes())
            rid = second['technical_precheck']['selected'][0]
            catalog = p.load(root / 'data.json')
            next(r for r in catalog['records'] if r['id'] == rid)['note'] += ' changed'
            (root / 'data.json').write_text(json.dumps(catalog), encoding='utf8')
            third = p.prepare(root, NOW, 3, 2, fetch, lambda _: None)
            before = {t['id']: t for t in second['technical_precheck']['normative_queue']}
            after = {t['id']: t for t in third['technical_precheck']['normative_queue']}
            self.assertNotEqual(before[rid]['task_version'], after[rid]['task_version'])


if __name__ == '__main__':
    unittest.main()
