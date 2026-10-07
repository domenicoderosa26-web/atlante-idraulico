#!/usr/bin/env python3
"""Canonical topics: normalize candidates, validate publication, preserve JSON text."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / 'topic-taxonomy.json'


def key(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', str(value))
                           if not unicodedata.combining(c)).casefold().split())


def load_taxonomy(path=TAXONOMY_PATH):
    taxonomy = json.loads(Path(path).read_text(encoding='utf-8'))
    categories = taxonomy['categories']
    if len(categories) != 14:
        raise ValueError('La tassonomia deve contenere esattamente 14 argomenti')
    ids, labels, aliases = set(), set(), set()
    for category in categories:
        cid, label = category['id'], category['label']
        if not cid or not label.strip() or cid in ids or key(label) in labels:
            raise ValueError('Tassonomia: categoria vuota o duplicata')
        ids.add(cid)
        labels.add(key(label))
        for alias in [label, *category.get('aliases', [])]:
            if key(alias) in aliases:
                raise ValueError('Tassonomia: alias duplicato ' + alias)
            aliases.add(key(alias))
    for alias in taxonomy['context_aliases']:
        if key(alias) in aliases or key(alias) in labels:
            raise ValueError('Tassonomia: alias contestuale duplicato ' + alias)
        aliases.add(key(alias))
    for rule in taxonomy['inference_rules']:
        if not set(rule['topics']) <= ids:
            raise ValueError('Tassonomia: categoria sconosciuta nella regola')
        for condition in rule['all']:
            re.compile(condition['pattern'])
    for review in taxonomy['reviewed_records'].values():
        if not set(review['topics'] + review.get('exclude_topics', [])) <= ids or not review['source_urls'] or not review['evidence']:
            raise ValueError('Tassonomia: revisione senza evidenza')
    return taxonomy


def source_urls(record):
    return {record.get('url', ''), record.get('document_url', ''),
            *(d.get('url', '') for d in record.get('documents', []))}


def review_matches(record, review):
    return bool(review and set(review['source_urls']) & source_urls(record)
                and any(all(record.get(field) == value for field, value in fields.items())
                        for fields in review.get('object_versions', [{}])))


def context_topics(record, taxonomy):
    """Identify the instrument from object fields and reviewed source evidence.

    Notes/history can mention a different plan: they never establish membership.
    Bare legacy tags or an authority/region alone never establish membership.
    """
    found = set()
    review = taxonomy['reviewed_records'].get(record.get('id'))
    reviewed = review_matches(record, review)
    if reviewed:
        found.update(review['topics'])
    object_text = key(record.get('title', '') + ' ' + record.get('ref', ''))
    mixed = bool(re.search(r'\bpai\b', object_text) and re.search(r'\bpgra\b', object_text))
    for rule in taxonomy['inference_rules']:
        if mixed and not reviewed:
            continue
        # Reviewed collections/framework acts have explicitly delimited scope.
        if reviewed:
            continue
        if set(rule.get('unless_topics', [])) & found:
            continue
        if all(re.search(condition['pattern'], key(' '.join(
                str(record.get(field, '')) for field in condition['fields'])))
               for condition in rule['all']):
            found.update(rule['topics'])
    # Optional manually verified metadata, with evidence linked on the record.
    for evidence in record.get('topic_evidence', []):
        if evidence.get('source') in source_urls(record) and evidence.get('note'):
            if evidence.get('category') not in {c['id'] for c in taxonomy['categories']}:
                raise ValueError('Evidenza con categoria sconosciuta: ' + record['id'])
            found.add(evidence['category'])
    return found


def normalize_record(record, taxonomy):
    out = copy.deepcopy(record)
    categories = taxonomy['categories']
    by_id = {c['id']: c for c in categories}
    direct = {key(a): c['id'] for c in categories for a in [c['label'], *c.get('aliases', [])]}
    contextual = {key(a): v['resolve'] for a, v in taxonomy['context_aliases'].items()}
    inferred = context_topics(record, taxonomy)
    review = taxonomy['reviewed_records'].get(record.get('id'))
    reviewed = review_matches(record, review)
    found, unresolved = set(inferred), []
    raw_topics = record.get('topics', [])
    if not isinstance(raw_topics, list) or any(not isinstance(t, str) or not t.strip() for t in raw_topics):
        raise ValueError('Argomenti non validi: ' + record['id'])
    # Retain unresolved input so running normalization twice cannot erase warnings.
    pending = record.get('topic_classification', {})
    raw_topics = list(dict.fromkeys(raw_topics + pending.get('unresolved', [])))
    for topic in raw_topics:
        # A source-bound, content-bound review determines the complete set,
        # rather than blindly carrying forward every old association.
        if reviewed and (key(topic) in direct or key(topic) in contextual):
            continue
        cid = direct.get(key(topic))
        if cid:
            if not by_id[cid].get('contextual') or cid in inferred:
                found.add(cid)
            else:
                unresolved.append(topic)
            continue
        mode = contextual.get(key(topic))
        candidates = {
            'plan': {c['id'] for c in categories if c.get('contextual')},
            'hydraulic': {'pai-idraulico', 'pgra', 'pzp'},
            'landslide': {'pai-frane', 'pai-geomorfologico'},
            'invariance': {'invarianza'},
            'water': {'demanio', 'scarichi', 'riuso'},
            'drainage': {'drenaggio', 'riuso', 'prima-pioggia'},
        }.get(mode, set())
        if not candidates & inferred:
            unresolved.append(topic)
    out['topics'] = sorted([c['label'] for c in categories if c['id'] in found], key=key)
    if unresolved or not out['topics']:
        out['topic_classification'] = {'status': 'argomento da classificare',
                                       'unresolved': unresolved or ['Nessun argomento riconosciuto']}
    else:
        out.pop('topic_classification', None)
    # Losing already canonical topics is a structural error, not an unknown import.
    old_canonical = {t for t in record.get('topics', []) if t in {c['label'] for c in categories}}
    if old_canonical and not out['topics']:
        raise ValueError('La normalizzazione elimina tutti gli argomenti: ' + record['id'])
    return out


def normalize_archive(archive, taxonomy=None):
    taxonomy = taxonomy or load_taxonomy()
    out = copy.deepcopy(archive)
    out['records'] = [normalize_record(r, taxonomy) for r in archive['records']]
    validate_archive(out, taxonomy)
    return out


def validate_archive(archive, taxonomy=None):
    taxonomy = taxonomy or load_taxonomy()
    allowed = {c['label'] for c in taxonomy['categories']}
    contextual = {c['label']: c['id'] for c in taxonomy['categories'] if c.get('contextual')}
    seen = set()
    for record in archive['records']:
        if record['id'] in seen:
            raise ValueError('ID duplicato: ' + record['id'])
        seen.add(record['id'])
        topics = record.get('topics')
        if not isinstance(topics, list) or any(t not in allowed for t in topics):
            raise ValueError('Argomento fuori tassonomia: ' + record['id'])
        if len(topics) != len(set(topics)):
            raise ValueError('Argomento duplicato: ' + record['id'])
        pending = record.get('topic_classification', {})
        if not topics or pending:
            raise ValueError('Argomenti assenti o da classificare: ' + record['id'])
        evidence = context_topics(record, taxonomy)
        if any(contextual[t] not in evidence for t in topics if t in contextual):
            raise ValueError('Strumento di piano non comprovato: ' + record['id'])


def replace_fields(text, old, new):
    """Only change topics and classification metadata; keep all other bytes."""
    decoder = json.JSONDecoder()
    start = re.search(r'"records"\s*:\s*\[', text).end()
    changes = []
    for previous, updated in zip(old['records'], new['records']):
        start = re.search(r'\S', text[start:]).start() + start
        if text[start] == ',':
            start = re.search(r'\S', text[start+1:]).start() + start+1
        obj, end = decoder.raw_decode(text, start)
        if obj != previous:
            raise ValueError('Impossibile preservare il formato JSON')
        block = text[start:end]
        for field in ['topics', 'topic_classification']:
            if previous.get(field) == updated.get(field):
                continue
            match = re.search(r'"' + field + r'"\s*:\s*', block)
            value = json.dumps(updated[field], ensure_ascii=False) if field in updated else None
            if match:
                value_start = match.end()
                _, value_end = decoder.raw_decode(block, value_start)
                old_raw = block[value_start:value_end]
                if value is not None:
                    if '\n' in old_raw:
                        indent = re.search(r'\n([ \t]*)', old_raw).group(1)
                        value = '[\n' + ',\n'.join(indent+json.dumps(t,ensure_ascii=False) for t in updated[field]) + '\n' + indent[:-2] + ']'
                    block = block[:value_start] + value + block[value_end:]
                else:
                    # Classification metadata is added as the final property by this tool.
                    field_start = block.rfind(',', 0, match.start())
                    if field_start < 0 or block[value_end:].strip() != '}':
                        raise ValueError('Metadati da rimuovere manualmente: ' + previous['id'])
                    block = block[:field_start] + block[value_end:]
            else:
                closing = block.rfind('}')
                block = block[:closing].rstrip() + ', "' + field + '": ' + value + block[closing:]
        changes.append((start, end, block))
        start = end
    for begin, end, block in reversed(changes):
        text = text[:begin] + block + text[end:]
    if json.loads(text) != new:
        raise ValueError('Migrazione JSON discordante')
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['normalize', 'validate'])
    p.add_argument('paths', nargs='+')
    args = p.parse_args()
    taxonomy = load_taxonomy()
    staged = []
    for name in args.paths:
        path = Path(name)
        text = path.read_text(encoding='utf-8')
        old = json.loads(text)
        if args.command == 'validate':
            validate_archive(old, taxonomy)
            print(f'{name}: {len(old["records"])} schede valide')
            continue
        new = normalize_archive(old, taxonomy)
        pending = [r for r in new['records'] if r.get('topic_classification')]
        for record in pending:
            print(f'{record["id"]}: argomento da classificare: {record["topic_classification"]["unresolved"]}', file=sys.stderr)
        staged.append((path, replace_fields(text, old, new)))
        print(f'{name}: {len(new["records"])} schede; {len(pending)} da classificare')
    # No source is touched until all candidate archives validate.
    for path, text in staged:
        if text != path.read_text(encoding='utf-8'):
            temp = path.with_suffix(path.suffix + '.tmp')
            temp.write_text(text, encoding='utf-8')
            os.replace(temp, path)


if __name__ == '__main__':
    main()
