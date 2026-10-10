"""Bounded technical preparation of existing Phase 3 work; never a legal review."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from documentary import record_version

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = Path('docs/audit/progress.json')
SEED = Path('docs/audit/2026-10-10/completamento/ricevute-accesso.json')
NOTICE = 'Controllo tecnico: identità candidata, disponibilità e variazioni non attestano contenuto, vigenza o abrogazione.'
MAX_BYTES = 2_000_000


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def valid_url(url, hosts):
    try:
        p = urlsplit(url)
        return p.scheme == 'https' and p.hostname in hosts and not p.username and not p.password and p.port in (None, 443)
    except ValueError:
        return False


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not valid_url(newurl, self.hosts):
            raise ValueError('Redirect fuori dalla lista istituzionale autorizzata')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def usable(receipt):
    return (receipt.get('http_status') == 200 and not receipt.get('access_challenge')
            and not receipt.get('empty_response') and bool(receipt.get('sha256') or receipt.get('sample_sha256')))


def due(receipt, now):
    try:
        checked = dt.datetime.fromisoformat(receipt['checked_at'])
        age = (now - checked).total_seconds()
        return age < 0 or age >= (7 * 86400 if usable(receipt) else 86400)
    except (KeyError, TypeError, ValueError):
        return True


def check(url, old, hosts, now, opener=None):
    result = {'url': url, 'checked_at': now.isoformat(), 'semantic_verification': 'not_performed_by_access_check'}
    if not valid_url(url, hosts):
        return dict(result, error='URL non autorizzato', technical_state='blocked')
    headers = {'User-Agent': 'Atlante-Idraulico-Precheck/1.0', 'Accept-Encoding': 'identity'}
    # Validators are used only for a previously observed complete representation.
    if old.get('sha256') and old.get('body_complete'):
        for field, header in [('etag', 'If-None-Match'), ('last_modified', 'If-Modified-Since')]:
            if old.get(field):
                headers[header] = old[field]
    opener = opener or urllib.request.build_opener(SafeRedirect(hosts)).open
    try:
        with opener(urllib.request.Request(url, headers=headers), timeout=12) as response:
            if not valid_url(response.geturl(), hosts):
                raise ValueError('Destinazione non autorizzata')
            body = response.read(MAX_BYTES + 1)
            complete = len(body) <= MAX_BYTES
            body = body[:MAX_BYTES]
            pdf = body.startswith(b'%PDF-')
            html = body[:200_000].decode('utf-8', errors='replace') if not pdf else ''
            title = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
            challenge = bool(re.search(r'captcha|access denied|just a moment|verifica di sicurezza', html, re.I))
            digest = hashlib.sha256(body).hexdigest()
            field = 'sha256' if complete else 'sample_sha256'
            result.update(http_status=response.status, final_url=response.geturl(),
                          content_type=response.headers.get('Content-Type', ''),
                          etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'),
                          body_complete=complete, sample_bytes=len(body), content_signature='pdf' if pdf else 'html' if title else 'unknown',
                          empty_response=not body, access_challenge=challenge,
                          identity_candidate=re.sub(r'\s+', ' ', title.group(1))[:300] if title else None,
                          identity_basis='HTML title only' if title else 'PDF signature only' if pdf else 'not_detected',
                          technical_state='available' if response.status == 200 and body and not challenge else 'needs_attention')
            result[field] = digest
            comparable = old.get(field) and (complete or old.get('sample_bytes') == len(body))
            result['variation'] = ('different' if old[field] != digest else 'same') if comparable else 'unknown'
            result['comparison_scope'] = 'complete_bytes' if complete else 'prefix_only'
            if comparable and old[field] != digest:
                result['previous_observation'] = {'checked_at': old.get('checked_at'), field: old[field]}
            if pdf and not complete:
                result['technical_state'] = 'partial_pdf'
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and old.get('sha256') and old.get('body_complete'):
            result = dict(old, checked_at=now.isoformat(), http_status=200,
                          revalidation_http_status=304, variation='same', comparison_scope='server_validator')
        else:
            result.update(http_status=exc.code, error=str(exc)[:300], technical_state='needs_attention')
        exc.close()
    except (OSError, ValueError) as exc:
        result.update(error=str(exc)[:300], technical_state='needs_attention')
    return result


def prepare(root, now, batch_size=3, max_requests=8, fetch=check, sleep=time.sleep):
    progress = load(root / PROGRESS)
    residual_path = Path(progress['residual_queue'])
    if residual_path.is_absolute() or '..' in residual_path.parts or not residual_path.as_posix().startswith('docs/audit/'):
        raise ValueError('Coda fuori da docs/audit')
    residual = load(root / residual_path)['records']
    catalog = {r['id']: r for r in load(root / 'data.json')['records']}
    hosts = set(load(root / 'scripts/precheck-hosts.json')['hosts'])
    previous = progress.get('technical_precheck', {})
    receipts = {r['url']: r for r in load(root / SEED)['receipts']}
    receipts.update(previous.get('receipts', {}))
    tasks = {}
    for row in residual:
        rid = row['id']
        operations = row.get('next_step') or row.get('needed_source_or_operation') or []
        if not operations or rid not in catalog:
            continue
        state = progress['records'].get(rid, {})
        record = catalog[rid]
        urls = sorted(set(state.get('source_urls', []) + [record['url']] +
                          [d['url'] for d in record.get('documents', [])] +
                          [x['url'] for x in row.get('actual_access_problems', [])] +
                          [x['source_url'] for x in row.get('verified_findings', [])]))
        key = fingerprint([record_version(record), operations, urls])
        tasks[rid] = {'id': rid, 'task_version': key, 'operations': operations, 'source_urls': urls,
                      'existing_evidence': state.get('evidence'), 'limitations': row.get('limitations', []),
                      'requires_substantive_review': True}
    # Prefer the existing next batch, then oldest preparation. Changed tasks become due immediately.
    preferred = progress.get('next_batch', [])
    completed = previous.get('tasks', {})
    eligible = [rid for rid, task in tasks.items() if completed.get(rid, {}).get('task_version') != task['task_version']
                or due({'checked_at': completed.get(rid, {}).get('prepared_at'), 'http_status': 200, 'sha256': 'task'}, now)
                or any(due(receipts.get(u, {}), now) for u in task['source_urls'])]
    eligible.sort(key=lambda rid: (completed.get(rid, {}).get('prepared_at', '') if completed.get(rid, {}).get('task_version') == tasks[rid]['task_version'] else '',
                                   preferred.index(rid) if rid in preferred else len(preferred), rid))
    selected = eligible[:batch_size]
    used = 0
    touched = set()
    for rid in selected:
        finished = True
        for url in tasks[rid]['source_urls']:
            if url in touched or not due(receipts.get(url, {}), now):
                continue
            if not valid_url(url, hosts):
                receipts[url] = dict(url=url, checked_at=now.isoformat(), technical_state='blocked', error='URL non autorizzato', semantic_verification='not_performed_by_access_check')
                touched.add(url)
                continue
            if used >= max_requests:
                finished = False
                continue
            sleep(2)  # Sequential requests, including between different hosts.
            receipts[url] = fetch(url, receipts.get(url, {}), hosts, now)
            touched.add(url)
            used += 1
        if finished:
            completed[rid] = {'task_version': tasks[rid]['task_version'], 'prepared_at': now.isoformat()}
    for rid, task in tasks.items():
        sources = [receipts.get(u, {'url': u, 'technical_state': 'not_checked'}) for u in task['source_urls']]
        pdf_urls = {d['url'] for d in catalog[rid].get('documents', []) if d.get('format', '').lower() == 'pdf'}
        documents = [{'url': r['url'], 'available': usable(r) and (r['url'] not in pdf_urls or r.get('content_signature') == 'pdf'),
                     'expected_pdf': r['url'] in pdf_urls, 'detected_signature': r.get('content_signature'),
                     'identity_candidate': r.get('identity_candidate'), 'body_complete': r.get('body_complete', False),
                     'checked_at': r.get('checked_at'), 'stale': due(r, now),
                     'technical_state': r.get('technical_state', 'legacy_receipt')} for r in sources]
        attention = any(not d['available'] or not d['body_complete'] or d['stale'] for d in documents) or any(r.get('variation') == 'different' for r in sources)
        task.update(priority='high' if attention else 'normal', priority_reason='Fonte incompleta, non accessibile, scaduta, non controllata o variata' if attention else 'Coordinamento normativo residuo',
                    documents=documents)
    # One extension of the existing registry, no second catalogue or PDF archive.
    progress['technical_precheck'] = {'schema_version': 1, 'notice': NOTICE,
        'source_queue': residual_path.as_posix(), 'selected': selected, 'requests': used,
        'tasks': {rid: value for rid, value in completed.items() if rid in tasks},
        'seed_receipts': SEED.as_posix(),
        'receipts': {u: r for u, r in receipts.items() if u in (set(previous.get('receipts', {})) | touched)
                     and u in {u for t in tasks.values() for u in t['source_urls']}},
        'normative_queue': sorted(tasks.values(), key=lambda t: (t['priority'] != 'high', t['id']))}
    return progress


def main():
    parser = argparse.ArgumentParser(description=NOTICE)
    parser.add_argument('--batch-size', type=int, choices=range(1, 6), default=3)
    parser.add_argument('--max-requests', type=int, choices=range(1, 13), default=8)
    parser.add_argument('--plan', action='store_true', help='No network and no writes')
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    if args.plan:
        result = prepare(ROOT, now, args.batch_size, args.max_requests,
                         fetch=lambda url, old, hosts, now: dict(old, url=url, technical_state='not_checked'), sleep=lambda _: None)
        print(json.dumps(result['technical_precheck'], ensure_ascii=False, indent=2))
    else:
        result = prepare(ROOT, now, args.batch_size, args.max_requests)
        path = ROOT / PROGRESS
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(path)
        print(NOTICE)
        print('Batch:', result['technical_precheck']['selected'], 'Requests:', result['technical_precheck']['requests'])


if __name__ == '__main__':
    main()
