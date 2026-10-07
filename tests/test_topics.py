import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from topics import load_taxonomy, normalize_archive, normalize_record, validate_archive, replace_fields
from normattiva import Client, monitor, UTC
import datetime as dt

ROOT = Path(__file__).parents[1]

class TopicTests(unittest.TestCase):
    def setUp(self):
        self.taxonomy = load_taxonomy()
        self.data = json.loads((ROOT / 'data.json').read_text())
        self.labels = {c['id']: c['label'] for c in self.taxonomy['categories']}

    def record(self, title, topics, **extra):
        return dict(id='new-act',title=title,ref='',summary='',topics=topics,url='https://example.gov/act',**extra)

    def test_all_archives_and_no_forbidden_aliases(self):
        forbidden = {'PAI','PAI e PGRA','PGRA','Pericolosità idraulica','Pericolosità e rischio idraulico',
                     'Pericolosità da alluvione','Pericolosità da frana','Pericolosità e rischio da frana','Attraversamenti'}
        for name in ['data.json','dist/data.json']:
            archive = json.loads((ROOT / name).read_text())
            validate_archive(archive, self.taxonomy)
            self.assertEqual(normalize_archive(archive, self.taxonomy), archive)
            self.assertTrue(all(r['topics'] for r in archive['records']))
            self.assertFalse(forbidden & {t for r in archive['records'] for t in r['topics']})
        self.assertEqual(len(normalize_archive(self.data,self.taxonomy)['records']),len(self.data['records']))
        # Every category has a real use in the primary archive; no empty menu options.
        self.assertEqual(set(self.labels.values()), {t for r in self.data['records'] for t in r['topics']})

    def test_alias_multi_topic_and_deduplication(self):
        row = self.record('Opere idrauliche', ['Attraversamenti','parallelismi','Demanio e polizia idraulica'])
        out = normalize_record(row,self.taxonomy)
        self.assertEqual(out['topics'],[self.labels['demanio'],self.labels['attraversamenti']])
        self.assertEqual(normalize_record(out,self.taxonomy),out)

    def test_instrument_not_inferred_from_generic_hazard_or_notes(self):
        row = self.record('Regolamento edilizio', ['Pericolosità idraulica'], note='Coordinamento con PGRA e PAI')
        out = normalize_record(row,self.taxonomy)
        self.assertEqual(out['topics'],[])
        self.assertEqual(out['topic_classification']['status'],'argomento da classificare')
        self.assertEqual(out['title'],row['title'])
        self.assertEqual(normalize_record(out,self.taxonomy),out)

    def test_pai_frane_hydraulic_and_pgra_are_distinct(self):
        for title, raw, expected in [
            ('Aggiornamento PAI rischio da frana',['PAI','Pericolosità e rischio da frana'],'pai-frane'),
            ('Variante PAI idraulica',['PAI e PGRA','Pericolosità idraulica'],'pai-idraulico'),
            ('Variante mappe PGRA',['PGRA','Pericolosità da alluvione'],'pgra'),
            ('Variante PAI geomorfologico',['PAI'],'pai-geomorfologico')]:
            out = normalize_record(self.record(title,raw),self.taxonomy)
            self.assertEqual(out['topics'],[self.labels[expected]])
            self.assertNotIn('topic_classification',out)

    def test_pzp_not_pai_and_framework_not_pgra(self):
        out = normalize_record(self.record('Modifica PZP per frana',['PZP','Frane']),self.taxonomy)
        self.assertEqual(set(out['topics']),{self.labels['pzp'],self.labels['dissesto']})
        rows = {r['id']:r for r in self.data['records']}
        for id in ['dl49','ueall','dl152','tos41','milano']:
            self.assertFalse(any(t.startswith(('PAI -','PGRA -')) for t in rows[id]['topics']))
        self.assertIn(self.labels['pai-geomorfologico'],rows['pai-puglia']['topics'])
        self.assertNotIn(self.labels['pai-frane'],rows['pai-puglia']['topics'])
        self.assertNotIn(self.labels['compatibilita'],rows['bz-campo-tures-pzp-799-2026']['topics'])
        self.assertIn(self.labels['riuso'],rows['dl152']['topics'])
        self.assertEqual(set(rows['dist-alpi']['topics']),{self.labels['pgra'],self.labels['compatibilita']})

    def test_unreviewed_mixed_collection_requires_evidence(self):
        row=self.record('PAI / PGRA raccolta',['PAI e PGRA'])
        out=normalize_record(row,self.taxonomy)
        self.assertEqual(out['topics'],[])
        row['topic_evidence']=[{'category':'pgra','source':row['url'],'note':'Relazione PGRA verificata'}]
        out=normalize_record(row,self.taxonomy)
        self.assertEqual(out['topics'],[self.labels['pgra']])

    def test_unknown_import_retains_record_and_warns(self):
        row=self.record('Documento non classificato',['Categoria arbitraria'])
        out=normalize_archive({'records':[row]},self.taxonomy)
        self.assertEqual(len(out['records']),1)
        self.assertEqual(out['records'][0]['url'],row['url'])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'candidate.json';path.write_text(json.dumps({'records':[row]}))
            result=subprocess.run([sys.executable,str(ROOT/'scripts/topics.py'),'normalize',str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('argomento da classificare',result.stderr)
            saved=json.loads(path.read_text());self.assertEqual(saved,out)

    def test_invalid_publication_fails_and_no_source_mutation(self):
        for topics in [['PAI'],[],[self.labels['pgra']], [self.labels['demanio']]*2]:
            with self.assertRaises(ValueError):
                validate_archive({'records':[self.record('Regolamento edilizio',topics)]},self.taxonomy)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'candidate.json';raw='{"records": [{"id":"bad", "title":"x", "topics": [null]}]}'
            path.write_text(raw)
            result=subprocess.run([sys.executable,str(ROOT/'scripts/topics.py'),'normalize',str(path)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertEqual(path.read_text(),raw)

    def test_duplicate_or_blank_taxonomy_rejected(self):
        for variant in ['duplicate','blank','alias']:
            t=copy.deepcopy(self.taxonomy)
            if variant=='duplicate':t['categories'].append(t['categories'][0])
            elif variant=='blank':t['categories'][0]['label']=' '
            else:t['categories'][1]['aliases'].append(t['categories'][0]['label'])
            with tempfile.TemporaryDirectory() as temp:
                p=Path(temp)/'taxonomy.json';p.write_text(json.dumps(t))
                with self.assertRaises(ValueError):load_taxonomy(p)

    def test_migration_preserves_all_other_fields_and_bytes(self):
        raw='{"records":[{"id":"new-act", "title":"Example", "topics": ["Attraversamenti"], "url":"https://example.gov/act"}], "version":42}\n'
        old=json.loads(raw);new=normalize_archive(old,self.taxonomy)
        migrated=replace_fields(raw,old,new)
        self.assertEqual(migrated,raw.replace('"Attraversamenti"',json.dumps(self.labels['attraversamenti'])))
        self.assertEqual({k:v for k,v in old['records'][0].items() if k!='topics'},
                         {k:v for k,v in new['records'][0].items() if k!='topics'})

    def test_daily_import_simulation_and_national_monitor(self):
        row=self.record('Variante PAI rischio idraulico',['PAI','Pericolosità e rischio idraulico','Attraversamenti'])
        candidate=copy.deepcopy(self.data);candidate['records'].append(row)
        out=normalize_archive(candidate,self.taxonomy)
        validate_archive(out,self.taxonomy)
        self.assertEqual(len(out['records']),len(self.data['records'])+1)
        self.assertEqual(out['records'][-1]['topics'],[self.labels['attraversamenti'],self.labels['pai-idraulico']])
        registry=json.loads((ROOT/'national.json').read_text())
        now=dt.datetime(2026,10,7,tzinfo=UTC)
        new,state,events=monitor(registry,{'last_successful_end':'2026-10-06T00:00:00Z'},
            Client(lambda path,payload:{'listaAtti':[],'numeroPagine':1,'numeroAttiTrovati':0}),now)
        self.assertEqual(new,registry);self.assertEqual(events,[])
        self.assertEqual(state['last_successful_end'],'2026-10-07T00:00:00Z')
        validate_archive(out,self.taxonomy)

if __name__=='__main__':unittest.main()
