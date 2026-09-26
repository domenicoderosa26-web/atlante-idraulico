import datetime as dt
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from normattiva import Client, APIError, monitor, validate, UTC

URN = 'urn:nir:stato:regio.decreto:1904-07-25;523'
ROW = dict(id='rd523', urn=URN, date='1904-07-25', number=523, act_type='REGIO DECRETO',
           editorial_code=None, status='DA VERIFICARE', title_full='R.D. 523',
           permalink='https://www.normattiva.it/uri-res/N2Ls?' + URN)
NOW = dt.datetime(2026, 9, 26, tzinfo=UTC)
STATE = {'last_successful_end':'2026-09-23T00:00:00Z'}

class Tests(unittest.TestCase):
    def test_real_registry(self):
        root = Path(__file__).parents[1]
        registry = json.loads((root / 'national.json').read_text())
        records = json.loads((root / 'data.json').read_text())['records']
        validate(registry, records)
        self.assertEqual(len(registry['acts']), 18)

    def test_empty_and_unchanged(self):
        reg = {'acts':[ROW.copy()]}
        for acts in ([], [{'annoProvvedimento':'2020','meseProvvedimento':'1','giornoProvvedimento':'1','numeroProvvedimento':'1'}]):
            def transport(path, payload):
                return {'listaAtti':acts,'numeroPagine':1,'numeroAttiTrovati':len(acts),'message':None}
            out, state, events = monitor(reg, STATE, Client(transport), NOW)
            self.assertEqual(out, reg)
            self.assertEqual(events, [])
            self.assertEqual(state['last_successful_end'],'2026-09-26T00:00:00Z')

    def test_changed(self):
        item = dict(annoProvvedimento='1904',meseProvvedimento='7',giornoProvvedimento='25',
                    numeroProvvedimento='523',denominazioneAtto='REGIO DECRETO',
                    dataUltimaModifica='2026-09-25',ultimiAttiModificanti='26A00001')
        def transport(path, payload):
            if path.endswith('aggiornati'):
                return {'listaAtti':[item], 'numeroPagine':1,'numeroAttiTrovati':1}
            return {'data':{'atto':dict(item,titolo='REGIO DECRETO 25 luglio 1904, n. 523')}}
        out, state, events = monitor({'acts':[ROW.copy()]}, STATE, Client(transport), NOW)
        self.assertEqual(out['acts'][0]['status'],'MODIFICATA')
        self.assertEqual(events[0]['amending_code'],'26A00001')
        self.assertTrue(events[0]['manual_review'])

    def test_error_and_incomplete_preserve_inputs(self):
        reg = {'acts':[ROW.copy()]}; state = STATE.copy()
        for transport in (lambda path,payload: (_ for _ in ()).throw(APIError('503')),
                          lambda path,payload: {'listaAtti':[], 'numeroPagine':2}):
            with self.assertRaises(APIError):
                monitor(reg, state, Client(transport), NOW)
            self.assertEqual(reg['acts'][0]['status'],'DA VERIFICARE')
            self.assertEqual(state, STATE)

    def test_gap_split(self):
        seen=[]
        def transport(path,payload):
            seen.append(payload);return {'listaAtti':[], 'numeroPagine':1,'numeroAttiTrovati':0}
        monitor({'acts':[ROW.copy()]}, {'last_successful_end':'2026-08-01T00:00:00Z'}, Client(transport), NOW)
        self.assertGreater(len(seen), 7)
        self.assertEqual(seen[0]['dataInizioAggiornamento'],'2026-08-01T00:00:00.000Z')

if __name__ == '__main__': unittest.main()
