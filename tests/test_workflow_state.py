import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from workflow_state import already_complete, validate_state, check
from normattiva import Client, APIError, monitor, public_status, UTC

class WorkflowTests(unittest.TestCase):
    def test_first_run_and_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'checkpoint.json'
            now = dt.datetime(2026, 9, 27, 7, 20, tzinfo=UTC)
            self.assertFalse(already_complete(path, now))
            path.write_text(json.dumps({'last_successful_end': '2026-09-27T05:18:00Z'}))
            self.assertTrue(already_complete(path, now))
            self.assertFalse(already_complete(path, now + dt.timedelta(days=1)))
            path.write_text('{invalid')
            with self.assertRaises(json.JSONDecodeError): validate_state(path)

    def test_zero_changes_public_status(self):
        now = dt.datetime(2026, 9, 27, 5, 18, tzinfo=UTC)
        s = public_status(now, 0)
        self.assertEqual(s['changes_detected'], 0)
        self.assertEqual(s['last_completed_at'], '2026-09-27T07:18:00+02:00')
        self.assertEqual(s['sources'], ['Normattiva Open Data: normativa nazionale'])

    def test_retry_transient_then_failure_preserves_inputs(self):
        import unittest.mock as mock
        row={'id':'rd523','urn':'urn:nir:stato:regio.decreto:1904-07-25;523'}
        registry={'acts':[row]}; state={'last_successful_end':'2026-09-26T00:00:00Z'}
        attempts=[]
        def fail(path, payload):
            attempts.append(path)
            raise APIError('temporaneamente indisponibile')
        with mock.patch('normattiva.time.sleep'):
            with self.assertRaises(APIError):
                monitor(registry, state, Client(fail), dt.datetime(2026,9,27,tzinfo=UTC))
        self.assertEqual(len(attempts), 3)
        self.assertEqual(state['last_successful_end'],'2026-09-26T00:00:00Z')
        self.assertEqual(registry['acts'][0],row)

if __name__ == '__main__': unittest.main()
