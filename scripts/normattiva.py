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
            try:
                result = self.transport(path, payload)
                if not isinstance(result, dict) or result.get('code') not in (None, '0', 0):
                    raise APIError('Risposta API anomala: ' + str(result.get('message') if isinstance(result, dict) else result)[:140])
                return result
            except (urllib.error.URLError, TimeoutError, APIError, ValueError) as exc:
                if attempt == 2:
                    raise APIError(f'{path}: {exc}') from exc
                time.sleep(2 ** attempt)

    def updated(self, start, end):
        result = self.post('/ricerca/aggiornati', {
            'dataInizioAggiornamento': start.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            'dataFineAggiornamento': end.isoformat(timespec='milliseconds').replace('+00:00', 'Z')})
        acts = result.get('listaAtti')
        if not isinstance(acts, list) or result.get('numeroPagine') not in (1, '1'):
            raise APIError('Elenco incompleto o paginato: finestra da suddividere manualmente')
        total = result.get('numeroAttiTrovati')
        if total is not None and int(total) != len(acts):
            raise APIError('Numero di atti discordante')
        return acts

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
    return got == (expected[0], expected[1], expected[2], str(row['number']).lstrip('0'))


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
                # The update feed reports modifications, not whole-act repeal status.
                row['status'] = 'MODIFICATA' if before != 'ABROGATA' else 'DA VERIFICARE'
                row['status_note'] = 'Aggiornamento rilevato; vigenza delle singole disposizioni da verificare.'
                row['amending_act'] = item.get('ultimiAttiModificanti') or row.get('amending_act')
                events.append({'checked_at': stamp(now), 'id': row['id'], 'urn': row['urn'],
                    'change': 'Modifica rilevata nell’elenco ufficiale', 'previous_status': before,
                    'new_status': row['status'], 'source': BASE + '/ricerca/aggiornati',
                    'api_error': None, 'manual_review': True, 'last_update': updated,
                    'amending_code': row['amending_act']})
    checkpoint['last_successful_end'] = stamp(now)
    return out, checkpoint, events


def write_atomic(path, obj):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, dest)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--registry', default='national.json')
    p.add_argument('--data', default='data.json')
    p.add_argument('--state', default='monitor-state/checkpoint.json')
    p.add_argument('--log', default='monitor-state/events.json')
    args = p.parse_args()
    registry = json.loads(Path(args.registry).read_text())
    validate(registry, json.loads(Path(args.data).read_text())['records'])
    now = utcnow()
    state_file = Path(args.state)
    state = json.loads(state_file.read_text()) if state_file.exists() else {'last_successful_end': stamp(now - dt.timedelta(days=7))}
    log_file = Path(args.log)
    log = json.loads(log_file.read_text()) if log_file.exists() else []
    try:
        new_registry, new_state, events = monitor(registry, state, Client(), now)
        validate(new_registry, json.loads(Path(args.data).read_text())['records'])
    except (APIError, ValueError) as exc:
        log.append({'checked_at': stamp(now), 'id': None, 'urn': None, 'change': 'Controllo incompleto',
                    'previous_status': None, 'new_status': None, 'source': BASE,
                    'api_error': str(exc), 'manual_review': True})
        write_atomic(log_file, log)
        print(str(exc), file=sys.stderr)
        return 1
    if events:
        new_registry['news'] = (events + registry.get('news', []))[:30]
        write_atomic(args.registry, new_registry)
    write_atomic(args.state, new_state)
    write_atomic(args.log, (log + events)[-500:])
    print(f'{len(events)} modifiche; checkpoint {new_state["last_successful_end"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
