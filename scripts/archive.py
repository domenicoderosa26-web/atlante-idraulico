#!/usr/bin/env python3
"""Validate the authoritative catalog and prevent obsolete distribution copies."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

from topics import validate_archive
from normattiva import validate as validate_national
from documentary import validate_review

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_catalog(data, baseline=None):
    require(isinstance(data, dict) and data.get('schemaVersion') == 1, 'Schema catalogo non valido')
    dt.date.fromisoformat(data['updatedAt'])
    require(isinstance(data.get('scope'), str), 'Ambito non valido')
    auto = data.get('automation')
    require(isinstance(auto, dict) and isinstance(auto.get('enabled'), bool)
            and all(isinstance(auto.get(k), str) for k in ['cadence', 'note']), 'Automazione non valida')
    for field in ['records', 'regions', 'districts', 'runs', 'news']:
        require(isinstance(data.get(field), list), 'Lista mancante: ' + field)
    require(bool(data['records']), 'Catalogo vuoto')
    require(all(isinstance(r, dict) for r in data['records']), 'Scheda non valida')
    ids = [r.get('id') for r in data['records']]
    require(all(isinstance(i, str) and i.strip() for i in ids), 'ID vuoto o non valido')
    require(len(set(ids)) == len(ids), 'ID duplicati')
    ids = set(ids)
    previous = {r['id']: r for r in baseline['records']} if baseline is not None else None
    names = [r['name'] for r in data['regions']]
    require(len(names) == len(set(names)), 'Regioni duplicate')
    for r in data['records']:
        for field in ['ref', 'title', 'level', 'date', 'url', 'summary', 'kind', 'status', 'source_kind', 'note', 'checked']:
            require(isinstance(r.get(field), str), r['id'] + ': campo non valido ' + field)
        for field in ['regions', 'topics', 'focus', 'relations', 'history']:
            require(isinstance(r.get(field), list), r['id'] + ': lista non valida ' + field)
        require(r['regions'] and set(r['regions']) <= set(names) | {'Italia', 'Unione europea'}, r['id'] + ': territorio sconosciuto')
        require(all(isinstance(v, str) for v in r['focus']), r['id'] + ': focus non valido')
        for rel in r['relations']:
            require(isinstance(rel, dict) and isinstance(rel.get('type'), str), r['id'] + ': relazione non valida')
            require(rel.get('id') in ids if 'id' in rel else bool(rel.get('text')), r['id'] + ': relazione senza destinazione')
        for h in r['history']:
            require(isinstance(h, dict) and all(isinstance(h.get(k), str) for k in ['date', 'text']), r['id'] + ': cronologia non valida')
        require(isinstance(r.get('documents', []), list), r['id'] + ': documenti non validi')
        for doc in r.get('documents', []):
            require(isinstance(doc, dict) and isinstance(doc.get('url'), str), r['id'] + ': documento senza URL')
        validate_review(r, previous.get(r['id'], {}) if previous is not None else None)
    # Check every regional ID list, including plan_ids and record_ids in thematic boxes.
    def references(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ['plan_ids', 'record_ids']:
                    require(isinstance(item, list) and all(i in ids for i in item), 'Riferimento territoriale inesistente')
                references(item)
        elif isinstance(value, list):
            for item in value:
                references(item)
    references(data['regions'])
    # Syntax/protocol only: this check does not assert institutional link availability.
    def urls(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if (key == 'url' or key.endswith('_url')) and item:
                    require(isinstance(item, str), 'URL non testuale')
                    url = urlsplit(item)
                    require(url.scheme == 'https' and bool(url.hostname), 'URL HTTPS non valido: ' + item)
                urls(item)
        elif isinstance(value, list):
            for item in value:
                urls(item)
    urls(data)
    validate_archive(data)
    if baseline is not None:
        for record in data['records']:
            old = previous.get(record['id'])
            if old:
                require(all(h in record['history'] for h in old['history']),
                        record['id'] + ': cronologia precedente rimossa')
        missing = {r['id'] for r in baseline['records']} - ids
        require(not missing, 'Schede perse rispetto alla base: ' + ', '.join(sorted(missing)))
        require(dt.date.fromisoformat(data['updatedAt']) >= dt.date.fromisoformat(baseline['updatedAt']),
                'Edizione del catalogo precedente alla base')
    return len(ids)


def validate_repository(root=ROOT, baseline=None):
    require(not (root / 'dist').exists(), 'dist/ reintroduce una distribuzione separata: usare i file nella radice')
    data = json.loads((root / 'data.json').read_text(encoding='utf-8'))
    count = validate_catalog(data, baseline)
    national = json.loads((root / 'national.json').read_text(encoding='utf-8'))
    validate_national(national, data['records'])
    json.loads((root / 'update-status.json').read_text(encoding='utf-8'))
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref', help='Git ref used only to check that no existing ID was lost')
    args = parser.parse_args()
    baseline = None
    if args.base_ref:
        baseline = json.loads(subprocess.check_output(['git', 'show', args.base_ref + ':data.json'], cwd=ROOT, text=True))
    print(f'data.json: {validate_repository(baseline=baseline)} schede valide; archivio unico')
