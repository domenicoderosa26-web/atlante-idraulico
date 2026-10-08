#!/usr/bin/env python3
"""Read-only monitor supervision; publish evidence separately from legal records."""
import argparse
import base64
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request
from zoneinfo import ZoneInfo
from normattiva import parse, stamp, utcnow, write_atomic

ROOT = Path(__file__).resolve().parents[1]
ROME = ZoneInfo('Europe/Rome')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def territorial_result(data):
    candidates = [(i, r) for i, r in enumerate(data.get('runs', []))
                  if 'territorial' in r.get('type', '').casefold()
                  or ('ciclo automatico' in r.get('type', '').casefold() and 'nazionale' not in r.get('type', '').casefold())]
    if not candidates:
        return {'state': 'non_documentato', 'date': None, 'evidence': 'data.json:runs', 'errors': []}
    i, row = max(candidates, key=lambda pair: pair[1]['date'])
    execution = row.get('execution') or {}
    outcome = execution.get('outcome')
    if outcome not in ('completato', 'parziale', 'fallito'):
        outcome = 'parziale' if row.get('errors') or 'parziale' in row.get('type', '').casefold() else 'documentato'
    # Legacy prose cannot certify an exhaustive cycle or an external platform job.
    if outcome == 'completato' and (not row.get('checked') or row.get('errors')):
        outcome = 'parziale'
    result = {'state': outcome, 'date': row['date'], 'evidence': f'data.json:runs[{i}]',
              'summary': row.get('summary'), 'sources_checked': row.get('checked', []),
              'source_urls': row.get('read_urls', []), 'territories': row.get('territories', []),
              'errors': row.get('errors', []), 'publication': execution.get('publication') or row.get('publication'),
              'external_execution_verified': False,
              'legacy_completion_marker': data.get('automation', {}).get('lastCompletedRun')}
    repeated = Counter()
    for _, item in sorted(candidates, key=lambda pair: pair[1]['date'], reverse=True)[:3]:
        for error in set(item.get('errors', [])):
            if any(term in error.casefold() for term in ['timeout', '502', '503', 'indisponib', 'errore interno']):
                repeated[error] += 1
    result['repeated_unavailability'] = [{'error': error, 'runs': count} for error, count in repeated.items() if count > 1]
    return result


def assess(data, status, checkpoint, runs, public_matches, now, prior=None, jobs=None, read_errors=None, receipt_errors=None):
    today = now.astimezone(ROME).date()
    national_runs = [r for r in runs if r.get('path') == '.github/workflows/normattiva.yml']
    latest = max(national_runs, key=lambda r: r['created_at']) if national_runs else None
    successful = status if status.get('outcome') == 'completato' else status.get('last_successful_result', {})
    completed = successful.get('last_completed_at')
    checkpoint_end = checkpoint.get('last_successful_end')
    consistent = bool(completed and checkpoint_end and parse(completed) == parse(checkpoint_end))
    fresh = bool(completed and parse(completed).astimezone(ROME).date() == today)
    matched = all(public_matches.values())
    state = 'completato' if fresh and consistent and matched and status.get('outcome') == 'completato' else 'in_attesa'
    anomalies = []
    active = bool(latest and latest['status'] != 'completed')
    def anomaly(code, severity, message, evidence):
        anomalies.append({'code': code, 'severity': severity, 'message': message, 'evidence': evidence})
    if active:
        state = 'in_corso'
    elif latest and latest.get('conclusion') not in ('success', 'skipped') and (not completed or parse(latest['created_at']) > parse(completed)):
        state = 'fallito'
        anomaly('NATIONAL_FAILED', 'error', 'Ultimo workflow nazionale fallito o interrotto; ultimo risultato valido conservato.', latest['html_url'])
    elif now.astimezone(ROME).hour >= 16 and not fresh and not read_errors:
        state = 'non_eseguito_entro_finestra'
        anomaly('NATIONAL_MISSING', 'error', 'Nessun controllo nazionale completato oggi entro la finestra delle 16:00 Europe/Rome.', latest.get('html_url') if latest else 'GitHub Actions: elenco esecuzioni')
    if status.get('outcome') == 'verificato':
        state = 'in_corso' if active else 'pubblicazione_non_confermata'
        anomaly('NATIONAL_PENDING', 'warning' if active else 'error', 'Verifica API documentata, pubblicazione non confermata.', status.get('run_url'))
    if not consistent:
        if state not in ('fallito', 'pubblicazione_non_confermata', 'in_corso'):
            state = 'non_allineato'
        anomaly('NATIONAL_CHECKPOINT', 'warning' if active else 'error', 'Stato completato e checkpoint interno non corrispondono.', 'update-status.json / normattiva-state:checkpoint.json')
    if any(value is False for value in public_matches.values()):
        if state not in ('fallito', 'non_allineato'):
            state = 'pubblicazione_non_confermata'
        anomaly('PUBLIC_DIVERGENCE', 'error', 'I file pubblici non corrispondono alla base del repository verificata.', public_matches)
    if receipt_errors:
        if not active and state != 'fallito': state = 'non_allineato'
        anomaly('NATIONAL_RECEIPT', 'warning' if active else 'error', 'I file del repository divergono dalla ricevuta interna.', receipt_errors)
    if read_errors:
        state = 'non_verificabile'
        for error in read_errors:
            anomaly('SUPERVISION_READ_ERROR', 'error', 'Una fonte tecnica non è stata acquisita: nessuna conclusione negativa per assenza.', error)
    national = {'state': state, 'last_completed_at': completed, 'expected_date': today.isoformat(),
                'deadline_local': '16:00 Europe/Rome', 'checkpoint_end': checkpoint_end,
                'checkpoint_consistent': consistent, 'latest_run': {k: latest.get(k) for k in ['id', 'html_url', 'event', 'status', 'conclusion', 'created_at', 'updated_at']} if latest else None,
                'scope': status.get('scope'), 'warnings': status.get('warnings', []), 'public_files_match': public_matches}
    if jobs is not None:
        national['jobs'] = [{k: job.get(k) for k in ['name', 'status', 'conclusion']} for job in jobs]
        national['api_step_executed'] = any(step.get('name') == 'Interroga Normattiva e valida i dati' and step.get('conclusion') == 'success' for job in jobs for step in job.get('steps', []))
    territorial = territorial_result(data)
    if territorial['state'] in ('parziale', 'fallito', 'non_documentato'):
        anomaly('TERRITORIAL_' + territorial['state'].upper(), 'warning', 'Il controllo territoriale è ' + territorial['state'] + '; la ricognizione non certifica tutte le fonti.', territorial['evidence'])
    if now.astimezone(ROME).hour >= 16 and territorial.get('date') != today.isoformat():
        anomaly('TERRITORIAL_MISSING', 'error', 'Nessuna ricognizione territoriale documentata oggi entro la finestra delle 16:00.', 'data.json:runs; esecutore esterno non interrogabile da questo workflow')
    if territorial.get('repeated_unavailability'):
        anomaly('TERRITORIAL_REPEATED_UNAVAILABILITY', 'warning', 'La stessa indisponibilità è documentata in più ricognizioni recenti.', territorial['repeated_unavailability'])
    prior = prior or {}
    events = {event['event_id']: event for event in prior.get('events', [])}
    for entry in anomalies:
        target = (latest or {}).get('id') if entry['code'].startswith('NATIONAL_') else territorial.get('date')
        event_id = sha(json.dumps([entry['code'], target, entry['evidence']], sort_keys=True, ensure_ascii=False).encode())[:24]
        entry['event_id'] = event_id
        if event_id not in events:
            events[event_id] = dict(entry, recorded_at=stamp(now))
    return {'schema_version': 1, 'checked_at': stamp(now), 'national': national, 'territorial': territorial,
            'anomalies': anomalies, 'events': list(events.values())[-100:],
            'has_errors': any(entry['severity'] == 'error' for entry in anomalies)}


def read_url(url, authenticated=False):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'AtlanteIdraulico/1.0'}
    if authenticated:
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as response:
                return response.read()
        except OSError:
            if attempt == 2: raise
            time.sleep(2 ** attempt)


def read_public_files(root, base, reader=read_url, wait=time.sleep, attempts=13):
    # A push may precede Pages. Allow a bounded deployment window before
    # recording a persistent divergence; an acquisition error remains unknown.
    for attempt in range(attempts):
        matches, errors = {}, []
        for name in ['data.json', 'national.json', 'update-status.json']:
            try:
                matches[name] = reader(base + name + '?v=' + str(time.time_ns())) == (root / name).read_bytes()
            except OSError as exc:
                matches[name] = None; errors.append('File pubblico ' + name + ': ' + str(exc))
        if errors or all(matches.values()) or attempt == attempts - 1:
            return matches, errors
        wait(10)


def collect():
    repo = os.environ['GITHUB_REPOSITORY']
    api = 'https://api.github.com/repos/' + repo
    base = 'https://domenicoderosa26-web.github.io/atlante-idraulico/'
    data = json.loads((ROOT / 'data.json').read_text())
    status = json.loads((ROOT / 'update-status.json').read_text())
    prior_path = ROOT / 'monitoring-status.json'
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
    errors, runs, checkpoint, jobs = [], [], {}, None
    try:
        for page in range(1, 4):
            page_runs = json.loads(read_url(api + f'/actions/runs?per_page=100&page={page}', True))['workflow_runs']
            runs += page_runs
            if len(page_runs) < 100 or any(r.get('path') == '.github/workflows/normattiva.yml' for r in page_runs): break
        else:
            errors.append('Elenco workflow troncato dopo 300 esecuzioni')
        candidates = [r for r in runs if r.get('path') == '.github/workflows/normattiva.yml']
        if candidates:
            latest = max(candidates, key=lambda r: r['created_at'])
            jobs = json.loads(read_url(api + '/actions/runs/' + str(latest['id']) + '/jobs?per_page=100', True))['jobs']
    except (OSError, ValueError, KeyError) as exc: errors.append('GitHub Actions: ' + str(exc))
    try:
        payload = json.loads(read_url(api + '/contents/checkpoint.json?ref=normattiva-state', True))
        checkpoint = json.loads(base64.b64decode(payload['content']))
    except (OSError, ValueError, KeyError) as exc: errors.append('Checkpoint: ' + str(exc))
    matches, public_errors = read_public_files(ROOT, base)
    errors += public_errors
    receipt_errors = []
    if checkpoint.get('national_sha256') and checkpoint['national_sha256'] != sha((ROOT / 'national.json').read_bytes()):
        receipt_errors.append('Hash del registro diverso dalla ricevuta tecnica')
    if checkpoint.get('status_sha256') and checkpoint['status_sha256'] != sha((ROOT / 'update-status.json').read_bytes()):
        receipt_errors.append('Hash dello stato diverso dalla ricevuta tecnica')
    report = assess(data, status, checkpoint, runs, matches, utcnow(), prior, jobs, errors, receipt_errors)
    report['repository_sha'] = os.environ.get('GITHUB_SHA')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='monitor-state/monitoring-status.json')
    args = parser.parse_args()
    report = collect(); write_atomic(args.output, report)
    print(json.dumps({'national': report['national']['state'], 'territorial': report['territorial']['state'], 'anomalies': report['anomalies']}, ensure_ascii=False))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as dest:
            dest.write('## Supervisione del monitoraggio\n\n')
            dest.write(f"Nazionale: **{report['national']['state']}**. Territoriale: **{report['territorial']['state']}**.\n\n")
            for entry in report['anomalies']: dest.write(f"- {entry['severity']}: {entry['message']}\n")
    return 0


if __name__ == '__main__': raise SystemExit(main())
