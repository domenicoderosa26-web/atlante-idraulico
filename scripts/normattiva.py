#!/usr/bin/env python3
"""Conservative national-act monitor; official Normattiva Open Data API only."""
import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo
from topics import validate_archive

BASE = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1'
VALID = {'VIGENTE', 'MODIFICATA', 'ABROGATA', 'PARZIALMENTE ABROGATA', 'DA VERIFICARE'}
UTC = dt.timezone.utc


def utcnow():
    return dt.datetime.now(UTC).replace(microsecond=0)


def parse(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(UTC)


def stamp(value):
    return value.astimezone(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')


def chunks(start, end):
    """Half-open windows, at most 7 days to stay below API 12-month/7000 limits."""
    while start < end:
        next_end = min(start + dt.timedelta(days=7), end)
        yield start, next_end
        start = next_end


class APIError(Exception):
    pass


class Client:
    def __init__(self, transport=None):
        self.transport = transport or self._request
        self.calls = []

    @staticmethod
    def _request(path, payload):
        req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
            headers={'Accept': 'application/json', 'Content-Type': 'application/json',
                     'Origin': 'https://dati.normattiva.it', 'User-Agent': 'AtlanteIdraulico/1.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.headers.get_content_type() != 'application/json':
                raise APIError('Risposta non JSON')
            return json.load(response)

    def post(self, path, payload):
        for attempt in range(3):
            if len(self.calls) >= 120:
                raise APIError('Limite di 120 richieste raggiunto: controllo incompleto, checkpoint conservato')
            evidence = {'endpoint': path, 'attempt': attempt + 1, 'requested_at': stamp(utcnow()), 'request': copy.deepcopy(payload)}
            self.calls.append(evidence)
            try:
                result = self.transport(path, payload)
                if not isinstance(result, dict) or result.get('code') not in (None, '0', 0):
                    raise APIError('Risposta API anomala: ' + str(result.get('message') if isinstance(result, dict) else result)[:140])
                evidence.update(outcome='success', pages=result.get('numeroPagine'), total=result.get('numeroAttiTrovati'))
                return result
            except (urllib.error.URLError, TimeoutError, APIError, ValueError) as exc:
                evidence.update(outcome='error', error=str(exc)[:500])
                if attempt == 2:
                    raise APIError(f'{path}: {exc}') from exc
                time.sleep(2 ** attempt)

    def updated(self, start, end):
        result = self.post('/ricerca/aggiornati', {
            'dataInizioAggiornamento': start.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            'dataFineAggiornamento': end.isoformat(timespec='milliseconds').replace('+00:00', 'Z')})
        acts = result.get('listaAtti')
        if not isinstance(acts, list):
            raise APIError('Elenco aggiornamenti incompleto')
        pages = result.get('numeroPagine')
        if pages not in (1, '1'):
            if isinstance(pages, (int, str)) and str(pages).isdigit() and int(pages) > 1 and end - start > dt.timedelta(hours=1):
                middle = start + (end - start) / 2
                return self.updated(start, middle) + self.updated(middle, end)
            raise APIError('Elenco incompleto o paginato anche nella finestra minima')
        total = result.get('numeroAttiTrovati')
        if total is not None and int(total) != len(acts):
            raise APIError('Numero di atti discordante')
        return acts

    def classification(self, row):
        parts = row['date'].split('-')
        base = {'denominazioneAtto': row['act_type'], 'annoProvvedimento': parts[0],
                'meseProvvedimento': str(int(parts[1])), 'giornoProvvedimento': str(int(parts[2])),
                'numeroProvvedimento': str(row['number']),
                'paginazione': {'paginaCorrente': 1, 'numeroElementiPerPagina': 20}}
        found = []
        for category, status in (('3', 'ABROGATA'), ('2', 'MODIFICATA'), ('1', 'VIGENTE')):
            result = self.post('/ricerca/avanzata', dict(base, classeProvvedimento=category))
            acts = result.get('listaAtti')
            if not isinstance(acts, list) or any(not isinstance(a, dict) for a in acts) or int(result.get('numeroPagine', 0)) > 1:
                raise APIError('Classificazione incompleta per ' + row['urn'])
            if result.get('numeroAttiTrovati') is not None and int(result['numeroAttiTrovati']) != len(acts):
                raise APIError('Conteggio classificazione discordante per ' + row['urn'])
            exact = [a for a in acts if matches(row, a) and
                     (not row.get('editorial_code') or a.get('codiceRedazionale') == row['editorial_code'])]
            if exact:
                if len(exact) != 1:
                    raise APIError('Identità multipla nella classificazione per ' + row['urn'])
                found.append(status)
        if len(found) != 1:
            raise APIError('Classificazione ambigua per ' + row['urn'] + ': ' + repr(found))
        return found[0]

    def detail(self, urn, editorial_code=None):
        result = self.post('/atto/dettaglio-atto-urn', {'urn': urn})
        data = result.get('data')
        if not isinstance(data, dict):
            raise APIError('Dettaglio assente per ' + urn)
        if isinstance(data.get('atto'), dict):
            return data['atto']
        candidates = [a for a in (data.get('lista') or []) if editorial_code and
                      '(' + editorial_code + ')' in str(a.get('sottoTitolo', ''))]
        if len(candidates) == 1:
            return candidates[0]
        raise APIError('Dettaglio assente o ambiguo per ' + urn)


def identity(act):
    return (str(act.get('annoProvvedimento', '')), str(act.get('meseProvvedimento', '')).zfill(2),
            str(act.get('giornoProvvedimento', '')).zfill(2), str(act.get('numeroProvvedimento', '')).lstrip('0'))


def matches(row, act):
    if not isinstance(act, dict):
        return False
    if row.get('editorial_code') and act.get('codiceRedazionale') == row['editorial_code']:
        return True
    if not row.get('urn') or not isinstance(act, dict):
        return False
    date = row['date'].split('-')
    return identity(act) == (date[0], date[1], date[2], str(row['number']).lstrip('0')) and (
        not row.get('act_type') or row['act_type'].upper() in str(act.get('denominazioneAtto', '')).upper())


def verify_detail(row, detail):
    expected = row['date'].split('-')
    got = identity(detail)
    same_type = not detail.get('denominazioneAtto') or row['act_type'].upper() in detail['denominazioneAtto'].upper()
    return same_type and got == (expected[0], expected[1], expected[2], str(row['number']).lstrip('0'))


def validate(registry, records):
    if not isinstance(registry, dict) or not isinstance(registry.get('acts'), list):
        raise ValueError('Registro nazionale non valido')
    ids = {r['id'] for r in records if r.get('level') == 'Nazionale'}
    seen = set()
    for row in registry['acts']:
        if row['id'] in seen or row['id'] not in ids:
            raise ValueError('ID nazionale duplicato o assente: ' + row['id'])
        seen.add(row['id'])
        if row['status'] not in VALID:
            raise ValueError('Stato non previsto: ' + row['id'])
        if row.get('urn') and not re.fullmatch(r'urn:nir:[a-z.]+:[a-z.]+:\d{4}-\d\d-\d\d(?:;[0-9A-Za-z]+)?', row['urn']):
            raise ValueError('URN non valido: ' + row['id'])
        if row.get('permalink') and row['permalink'] != 'https://www.normattiva.it/uri-res/N2Ls?' + row['urn']:
            raise ValueError('Permalink discordante: ' + row['id'])
        if row.get('official_pdf_url') and not row['official_pdf_url'].startswith('https://'):
            raise ValueError('PDF non HTTPS: ' + row['id'])
    if seen != ids:
        raise ValueError('Schede nazionali senza registro: ' + str(ids - seen))


def monitor(registry, state, client, now):
    """Return new registry, checkpoint and events. Never mutate inputs on failure."""
    out, checkpoint = copy.deepcopy(registry), copy.deepcopy(state)
    events = []
    start = parse(checkpoint['last_successful_end'])
    if start > now:
        raise APIError('Checkpoint nel futuro')
    index = {r['id']: r for r in out['acts'] if r.get('urn') and r.get('api_supported', True)}
    for begin, end in chunks(start, now):
        acts = client.updated(begin, end)
        for item in acts:
            if not isinstance(item, dict):
                raise APIError('Elemento aggiornamenti incompleto')
            for row in index.values():
                if not matches(row, item):
                    continue
                detail = client.detail(row['urn'], row.get('editorial_code'))
                if not verify_detail(row, detail):
                    raise APIError('Identità discordante per ' + row['urn'])
                before = row['status']
                updated = item.get('dataUltimaModifica')
                if not updated:
                    raise APIError('Data ultima modifica mancante per ' + row['urn'])
                if row.get('last_detected_update') == updated:
                    continue
                row['last_detected_update'] = updated
                row['last_checked'] = stamp(now)
                row['title_full'] = (detail.get('titolo') or row['title_full']) + (' — ' + detail['sottoTitolo'].strip() if detail.get('sottoTitolo') else '')
                row['editorial_code'] = item.get('codiceRedazionale') or row.get('editorial_code')
                # Official class 3 means repealed, 2 updated, 1 without updates.
                # Partial repeal cannot be established from this act-level classification.
                row['status'] = client.classification(row)
                row['status_note'] = 'Classe ufficiale Normattiva; applicabilità dei singoli articoli da verificare.'
                row['amending_act'] = item.get('ultimiAttiModificanti') or row.get('amending_act')
                events.append({'checked_at': stamp(now), 'id': row['id'], 'urn': row['urn'],
                    'change': 'Modifica rilevata nell’elenco ufficiale', 'previous_status': before,
                    'new_status': row['status'], 'source': BASE + '/ricerca/aggiornati',
                    'api_error': None, 'manual_review': True, 'last_update': updated,
                    'amending_code': row['amending_act']})
    checkpoint['last_successful_end'] = stamp(now)
    checkpoint['interval_start'] = stamp(start)
    checkpoint['phase'] = 'verificato'
    checkpoint.pop('publication_verified_at', None)
    checkpoint.pop('national_sha256', None)
    checkpoint.pop('status_sha256', None)
    return out, checkpoint, events


def write_atomic(path, obj):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, dest)


def public_status(now, changes, previous=None):
    # A completed API check is a candidate until both public files are verified.
    previous = previous or {}
    if previous.get('outcome') != 'completato':
        previous = previous.get('last_successful_result') or {}
    return {'last_completed_at': previous.get('last_completed_at'),
            'verification_completed_at': now.astimezone(ZoneInfo('Europe/Rome')).isoformat(timespec='seconds'),
            'timezone': 'Europe/Rome', 'outcome': 'verificato', 'publication_status': 'in_attesa',
            'sources': ['Normattiva Open Data: normativa nazionale'],
            'changes_detected': changes, 'changes_published': 0, 'warnings': [],
            'last_successful_result': previous}


def recover_events(previous, registry, events, checkpoint_start=None):
    recovered = []
    uncommitted_receipt = (checkpoint_start and previous.get('verification_completed_at')
                          and parse(previous['verification_completed_at']) > parse(checkpoint_start))
    if (previous.get('outcome') == 'verificato' or uncommitted_receipt) and previous.get('verification_completed_at'):
        end = parse(previous['verification_completed_at'])
        keys = {tuple(key) for key in previous.get('event_keys', [])}
        recovered = [event for event in registry.get('news', []) if (event.get('id'), event.get('last_update')) in keys
                     or (not keys and event.get('checked_at') and parse(event['checked_at']) == end)]
    unique = {(e['id'], e.get('last_update')): e for e in recovered + events}
    return list(unique.values())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--registry', default='national.json')
    p.add_argument('--data', default='data.json')
    p.add_argument('--state', default='monitor-state/checkpoint.json')
    p.add_argument('--log', default='monitor-state/events.json')
    p.add_argument('--public-status', default='update-status.json')
    args = p.parse_args()
    registry = json.loads(Path(args.registry).read_text())
    archive = json.loads(Path(args.data).read_text())
    validate_archive(archive)
    validate(registry, archive['records'])
    now = utcnow()
    state_file = Path(args.state)
    state = json.loads(state_file.read_text()) if state_file.exists() else {'last_successful_end': stamp(now - dt.timedelta(days=7))}
    log_file = Path(args.log)
    log = json.loads(log_file.read_text()) if log_file.exists() else []
    if not isinstance(log, list):
        raise ValueError('Log tecnico non valido')
    if not isinstance(state, dict) or 'last_successful_end' not in state:
        raise ValueError('Checkpoint non valido')
    previous = json.loads(Path(args.public_status).read_text()) if Path(args.public_status).exists() else {}
    client = Client()
    attempt = {'started_at': stamp(now), 'interval_start': state['last_successful_end'],
               'event': os.environ.get('GITHUB_EVENT_NAME'), 'outcome': 'in_corso'}
    attempt_path = state_file.parent / 'attempt.json'
    try:
        new_registry, new_state, events = monitor(registry, state, client, now)
        events = recover_events(previous, registry, events, state['last_successful_end'])
        validate(new_registry, json.loads(Path(args.data).read_text())['records'])
    except (APIError, ValueError) as exc:
        write_atomic(attempt_path, dict(attempt, outcome='fallito', error=str(exc), calls=client.calls))
        log.append({'checked_at': stamp(now), 'id': None, 'urn': None, 'change': 'Controllo incompleto',
                    'previous_status': None, 'new_status': None, 'source': BASE,
                    'api_error': str(exc), 'manual_review': True})
        write_atomic(log_file, log[-500:])
        print(str(exc), file=sys.stderr)
        return 1
    if events:
        unique_news = {}
        for event in events + registry.get('news', []):
            unique_news.setdefault((event['id'], event.get('last_update')), event)
        new_registry['news'] = list(unique_news.values())[:30]
        write_atomic(args.registry, new_registry)
    write_atomic(args.state, new_state)
    write_atomic(args.log, (log + events)[-500:])
    status = public_status(now, len(events), previous)
    eligible = [r['id'] for r in registry['acts'] if r.get('urn') and r.get('api_supported', True)]
    excluded = [r['id'] for r in registry['acts'] if r['id'] not in eligible]
    status['scope'] = {'monitored_ids': eligible, 'excluded_ids': excluded, 'total_records': len(registry['acts'])}
    if excluded:
        status['warnings'] = ['Controllo API limitato agli atti con URN supportato; esclusi: ' + ', '.join(excluded)]
    status['interval_start'] = state['last_successful_end']
    status['event_keys'] = [[event['id'], event.get('last_update')] for event in events]
    status['run_url'] = (os.environ.get('GITHUB_SERVER_URL', 'https://github.com') + '/' + os.environ['GITHUB_REPOSITORY']
                         + '/actions/runs/' + os.environ['GITHUB_RUN_ID']) if os.environ.get('GITHUB_RUN_ID') else None
    write_atomic(args.public_status, status)
    write_atomic(attempt_path, dict(attempt, outcome='verificato', verification_completed_at=stamp(now), calls=client.calls,
                                   monitored_ids=eligible, excluded_ids=excluded, changes_detected=len(events)))
    print(f'{len(events)} modifiche; checkpoint {new_state["last_successful_end"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
