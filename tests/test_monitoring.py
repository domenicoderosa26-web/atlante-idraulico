import copy
import datetime as dt
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from normattiva import APIError, Client, monitor, public_status, recover_events, UTC, main as national_main
from workflow_state import already_complete, complete_status, merge_state, public_matches, verify_public
from monitoring import assess, territorial_result
from test_normattiva import ROW, STATE, NOW

ROOT = Path(__file__).parents[1]


class ReliabilityTests(unittest.TestCase):
    def test_pending_result_and_publication_confirmation(self):
        old = {'outcome': 'completato', 'last_completed_at': '2026-09-25T07:18:00+02:00'}
        pending = public_status(NOW, 2, old)
        self.assertEqual(pending['outcome'], 'verificato')
        self.assertEqual(pending['changes_published'], 0)
        self.assertEqual(pending['last_completed_at'], old['last_completed_at'])
        complete = complete_status(pending)
        self.assertEqual(complete['changes_published'], 2)
        self.assertEqual(complete['last_completed_at'], pending['verification_completed_at'])
        with self.assertRaises(ValueError): complete_status(complete)

    def test_publication_requires_registry_and_status_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            status = Path(temp)/'update-status.json'; registry = Path(temp)/'national.json'
            status.write_bytes(b'{"outcome":"completato"}'); registry.write_bytes(b'{"acts":[]}')
            def opener(url, **kwargs): return io.BytesIO(status.read_bytes() if 'update-status' in url else b'{"acts":[1]}')
            self.assertFalse(public_matches('https://example.gov', status, registry, opener))
            def valid(url, **kwargs): return io.BytesIO(status.read_bytes() if 'update-status' in url else registry.read_bytes())
            self.assertTrue(public_matches('https://example.gov', status, registry, valid))
            with mock.patch('workflow_state.files_match', return_value=False), mock.patch('workflow_state.time.sleep'):
                with self.assertRaisesRegex(ValueError, 'checkpoint conservato'):
                    verify_public('https://example.gov', status, registry, request_build=False)

    def test_checkpoint_receipt_and_concurrent_newer_state(self):
        candidate = {'last_successful_end': '2026-09-26T00:00:00Z', 'phase':'pubblicato', 'publication_verified_at':'2026-09-26T00:01:00Z'}
        event = {'id':'rd523','last_update':'2026-09-25','change':'modifica','checked_at':'2026-09-26T00:00:00Z'}
        state, events = merge_state(STATE, candidate, [event], [event])
        self.assertEqual(events, [event]); self.assertEqual(state, candidate)
        with self.assertRaises(ValueError): merge_state({'last_successful_end':'2026-09-27T00:00:00Z'},candidate,[],[])
        with self.assertRaises(ValueError): merge_state(STATE,dict(candidate,phase='verificato'),[],[])

    def test_daily_idempotence_requires_valid_status_and_no_future_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'checkpoint.json';path.write_text(json.dumps({'last_successful_end':'2026-09-26T00:00:00Z'}))
            valid={'outcome':'completato','last_completed_at':'2026-09-26T02:00:00+02:00'}
            self.assertTrue(already_complete(path,NOW,valid))
            self.assertFalse(already_complete(path,NOW,dict(valid,outcome='verificato')))
            with self.assertRaises(ValueError): already_complete(path,NOW-dt.timedelta(seconds=1),valid)

    def test_dst_and_winter_timestamps(self):
        for now, suffix in [(dt.datetime(2026,7,1,tzinfo=UTC),'+02:00'),(dt.datetime(2026,12,1,tzinfo=UTC),'+01:00')]:
            self.assertTrue(public_status(now,0)['verification_completed_at'].endswith(suffix))

    def test_interrupted_main_preserves_registry_status_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp); registry=folder/'national.json'; status=folder/'update-status.json'; state=folder/'checkpoint.json'; log=folder/'events.json'
            registry.write_bytes((ROOT/'national.json').read_bytes());status.write_bytes((ROOT/'update-status.json').read_bytes());state.write_text(json.dumps(STATE))
            originals=[p.read_bytes() for p in [registry,status,state]]
            failing=Client(lambda path,payload:(_ for _ in ()).throw(APIError('timeout controllato')))
            argv=['normattiva','--registry',str(registry),'--data',str(ROOT/'data.json'),'--state',str(state),'--log',str(log),'--public-status',str(status)]
            with mock.patch('sys.argv',argv),mock.patch('normattiva.Client',return_value=failing),mock.patch('normattiva.time.sleep'):
                self.assertEqual(national_main(),1)
            self.assertEqual([p.read_bytes() for p in [registry,status,state]],originals)
            attempt=json.loads((folder/'attempt.json').read_text());self.assertEqual(attempt['outcome'],'fallito');self.assertEqual(len(attempt['calls']),3)
            self.assertEqual(len(json.loads(log.read_text())),1)

    def test_recovery_of_pending_events_survives_multiple_failed_publications(self):
        event={'id':'rd523','last_update':'2026-09-25','checked_at':'2026-09-26T00:00:00Z'}
        pending={'outcome':'verificato','verification_completed_at':'2026-09-27T00:00:00Z','event_keys':[['rd523','2026-09-25']]}
        recovered=recover_events(pending,{'news':[event]},[copy.deepcopy(event)])
        self.assertEqual(recovered,[event])
        self.assertEqual(recover_events(dict(pending,outcome='completato'),{'news':[event]},[]),[])
        complete=dict(pending,outcome='completato')
        self.assertEqual(recover_events(complete,{'news':[event]},[], '2026-09-26T00:00:00Z'),[event])
        self.assertEqual(recover_events(complete,{'news':[event]},[], '2026-09-27T00:00:00Z'),[])

    def test_pagination_recovers_interval_without_false_zero(self):
        seen=[]
        def transport(path,payload):
            start=dt.datetime.fromisoformat(payload['dataInizioAggiornamento'].replace('Z','+00:00'));end=dt.datetime.fromisoformat(payload['dataFineAggiornamento'].replace('Z','+00:00'))
            seen.append((start,end));return {'listaAtti':[], 'numeroPagine':2 if end-start>dt.timedelta(hours=1) else 1,'numeroAttiTrovati':0}
        client=Client(transport);self.assertEqual(client.updated(NOW,NOW+dt.timedelta(hours=2)),[]);self.assertEqual(len(seen),3)
        self.assertEqual(seen[1][1],seen[2][0])
        with self.assertRaises(APIError):Client(lambda p,v:{'listaAtti':[],'numeroPagine':2}).updated(NOW,NOW+dt.timedelta(minutes=30))

    def test_ambiguous_and_incomplete_classifications_do_not_advance(self):
        for result in [{'listaAtti':[{}], 'numeroPagine':1,'numeroAttiTrovati':2}, {'listaAtti':['invalid'],'numeroPagine':1}]:
            with self.assertRaises(APIError):Client(lambda p,v:result).classification(ROW)


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,10,8,14,20,tzinfo=UTC)
        self.status={'outcome':'completato','last_completed_at':'2026-10-08T07:30:00+02:00'}
        self.checkpoint={'last_successful_end':'2026-10-08T05:30:00Z'}
        self.run={'id':1,'path':'.github/workflows/normattiva.yml','created_at':'2026-10-08T05:18:00Z','status':'completed','conclusion':'success','html_url':'https://github.com/example/run/1'}
        self.data={'automation':{'lastCompletedRun':'2026-09-25'},'runs':[{'date':'2026-10-08','type':'Ciclo automatico territoriale · parziale','checked':['fonte A'],'errors':['timeout fonte A'],'territories':['Sardegna']}]}
        self.matches={n:True for n in ['data.json','national.json','update-status.json']}

    def result(self,**kwargs):
        args=dict(data=self.data,status=self.status,checkpoint=self.checkpoint,runs=[self.run],public_matches=self.matches,now=self.now);args.update(kwargs);return assess(**args)

    def test_distinct_success_and_partial_territorial_evidence(self):
        report=self.result();self.assertEqual(report['national']['state'],'completato');self.assertEqual(report['territorial']['state'],'parziale');self.assertFalse(report['has_errors']);self.assertFalse(report['territorial']['external_execution_verified'])
        self.assertEqual(report['territorial']['date'],'2026-10-08')

    def test_missing_run_only_after_grace_period(self):
        status=dict(self.status,last_completed_at='2026-10-07T07:30:00+02:00');checkpoint={'last_successful_end':'2026-10-07T05:30:00Z'}
        earlier=self.result(status=status,checkpoint=checkpoint,now=self.now-dt.timedelta(hours=5))
        self.assertEqual(earlier['national']['state'],'in_attesa')
        self.assertEqual(self.result(status=status,checkpoint=checkpoint)['national']['state'],'non_eseguito_entro_finestra')

    def test_failed_workflow_preserves_last_valid_result(self):
        failed=dict(self.run,id=2,created_at='2026-10-08T06:18:00Z',conclusion='failure')
        report=self.result(runs=[failed,self.run]);self.assertEqual(report['national']['state'],'fallito');self.assertEqual(report['national']['last_completed_at'],self.status['last_completed_at'])

    def test_pending_and_public_mismatch_are_not_success(self):
        pending=public_status(self.now,1,self.status);report=self.result(status=pending)
        self.assertEqual(report['national']['state'],'pubblicazione_non_confermata');self.assertTrue(report['has_errors'])
        bad=self.result(public_matches=dict(self.matches,**{'national.json':False}));self.assertTrue(bad['has_errors']);self.assertNotEqual(bad['national']['state'],'completato')

    def test_read_errors_cannot_prove_missing_execution(self):
        report=self.result(read_errors=['GitHub: timeout'],status={},checkpoint={})
        self.assertEqual(report['national']['state'],'non_verificabile');self.assertTrue(report['has_errors'])
        self.assertNotIn('NATIONAL_MISSING',[a['code'] for a in report['anomalies']])

    def test_active_publication_is_not_a_failed_cycle(self):
        pending=public_status(self.now,0,self.status)
        report=self.result(status=pending,runs=[dict(self.run,status='in_progress',conclusion=None)])
        self.assertEqual(report['national']['state'],'in_corso');self.assertFalse(report['has_errors'])

    def test_receipt_mismatch_cannot_certify_completion(self):
        report=self.result(receipt_errors=['Hash diverso'])
        self.assertEqual(report['national']['state'],'non_allineato');self.assertTrue(report['has_errors'])

    def test_error_events_are_not_duplicated(self):
        first=self.result();second=self.result(prior=first,now=self.now+dt.timedelta(minutes=1))
        self.assertEqual(first['events'],second['events'])

    def test_repeated_unavailability_is_source_backed(self):
        data=copy.deepcopy(self.data);data['runs'].append(dict(data['runs'][0],date='2026-10-07'))
        report=self.result(data=data);self.assertEqual(report['territorial']['repeated_unavailability'][0]['runs'],2)
        self.assertIn('TERRITORIAL_REPEATED_UNAVAILABILITY',[a['code'] for a in report['anomalies']])

    def test_new_record_does_not_certify_cycle_completion(self):
        data=copy.deepcopy(self.data);data['runs'][0]['execution']={'outcome':'completato'};data['runs'][0]['new_records']=['new-id']
        self.assertEqual(territorial_result(data)['state'],'parziale')


if __name__=='__main__':unittest.main()
