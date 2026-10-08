"""Publication receipts, daily idempotence and safe technical-state recovery."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo
from normattiva import parse, stamp, utcnow, validate, write_atomic
from topics import validate_archive


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def already_complete(path, now=None, status=None):
    file = Path(path)
    if not file.exists():
        return False
    state = json.loads(file.read_text())
    validate_state(path, now)
    current = now or utcnow()
    today = current.astimezone(ZoneInfo('Europe/Rome')).date()
    complete = parse(state['last_successful_end']).astimezone(ZoneInfo('Europe/Rome')).date() == today
    if status is not None:
        complete = complete and status.get('outcome') == 'completato' and bool(status.get('last_completed_at'))
        complete = complete and parse(status['last_completed_at']) == parse(state['last_successful_end'])
    return complete


def check(paths):
    national, data, status, checkpoint = [json.loads(Path(path).read_text()) for path in paths]
    validate_archive(data)
    validate(national, data['records'])
    if status['outcome'] not in ('verificato', 'completato') or status['timezone'] != 'Europe/Rome':
        raise ValueError('Stato pubblico non valido')
    for field in ['changes_detected', 'changes_published']:
        if not isinstance(status[field], int) or status[field] < 0:
            raise ValueError('Conteggio modifiche non valido')
    if status['outcome'] == 'verificato' and status['changes_published'] != 0:
        raise ValueError('Pubblicazione non ancora verificata')
    if status['outcome'] == 'completato' and status['changes_published'] != status['changes_detected']:
        raise ValueError('Conteggi pubblicati discordanti')
    end = status.get('verification_completed_at') or status.get('last_completed_at')
    if not end or parse(checkpoint['last_successful_end']) != parse(end):
        raise ValueError('Checkpoint e stato pubblico discordanti')


def validate_state(path, now=None):
    file = Path(path)
    if not file.exists():
        return
    state = json.loads(file.read_text())
    if not isinstance(state, dict) or 'last_successful_end' not in state:
        raise ValueError('Checkpoint non valido')
    end = parse(state['last_successful_end'])
    if end > (now or utcnow()):
        raise ValueError('Checkpoint nel futuro')


def complete_status(status):
    if status.get('outcome') != 'verificato' or not status.get('verification_completed_at'):
        raise ValueError('Risultato candidato non valido')
    result = dict(status)
    result.update(outcome='completato', publication_status='pubblicato',
                  last_completed_at=status['verification_completed_at'], changes_published=status['changes_detected'])
    result.pop('last_successful_result', None)
    return result


def files_match(site_url, paths, opener=urllib.request.urlopen):
    # Compare actual bytes, not only a timestamp: a stale registry is not a receipt.
    for name, path in paths:
        try:
            with opener(site_url.rstrip('/') + '/' + name + '?v=' + str(time.time_ns()), timeout=15) as response:
                body = response.read()
            if body != Path(path).read_bytes():
                return False
        except (OSError, ValueError):
            return False
    return True


def public_matches(site_url, status_path, national_path, opener=urllib.request.urlopen):
    return files_match(site_url, [('update-status.json', status_path), ('national.json', national_path)], opener)


def verify_files(site_url, paths, request_build=True):
    for attempt in range(24):
        if files_match(site_url, paths):
            return
        if attempt == 5 and request_build:
            request = urllib.request.Request(
                'https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/pages/builds',
                data=b'{}', method='POST', headers={
                    'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                    'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status not in (200, 201, 202):
                    raise ValueError('Build Pages non accettato')
        if attempt < 23:
            time.sleep(10)
    raise ValueError('Pages non serve i due file attesi: checkpoint conservato')


def verify_public(site_url, status_path, national_path, request_build=True):
    return verify_files(site_url, [('update-status.json', status_path), ('national.json', national_path)], request_build)


def merge_state(remote, candidate, remote_events, candidate_events):
    if candidate.get('phase') != 'pubblicato' or not candidate.get('publication_verified_at'):
        raise ValueError('Checkpoint senza ricevuta di pubblicazione')
    if remote and parse(remote['last_successful_end']) > parse(candidate['last_successful_end']):
        raise ValueError('Checkpoint remoto più recente: ripetere il controllo')
    combined = {}
    for event in remote_events + candidate_events:
        # Existing events retain their timestamps. A replay cannot duplicate them.
        identity = json.dumps([event.get(k) for k in ['id', 'last_update', 'change', 'api_error', 'checked_at']], ensure_ascii=False)
        combined[identity] = event
    return candidate, list(combined.values())[-500:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['validate-state', 'already-complete', 'validate', 'verify-public', 'verify-report', 'complete-status', 'receipt', 'merge-state'])
    parser.add_argument('paths', nargs='*')
    args = parser.parse_args()
    paths = args.paths
    if args.command == 'validate-state': validate_state(paths[0])
    elif args.command == 'already-complete':
        status = json.loads(Path(paths[1]).read_text()) if len(paths) > 1 else None
        complete = already_complete(paths[0], status=status)
        if complete and len(paths) > 2:
            complete = public_matches(os.environ['SITE_URL'], paths[1], paths[2])
        return 0 if complete else 1
    elif args.command == 'validate': check(paths)
    elif args.command == 'verify-public':
        verify_public(os.environ['SITE_URL'], paths[0], paths[1])
        print('Pages: registro nazionale e stato corrispondono ai file validati')
    elif args.command == 'verify-report':
        verify_files(os.environ['SITE_URL'], [('monitoring-status.json', paths[0])])
    elif args.command == 'complete-status':
        write_atomic(paths[0], complete_status(json.loads(Path(paths[0]).read_text())))
    elif args.command == 'receipt':
        status = json.loads(Path(paths[1]).read_text())
        if status.get('outcome') != 'completato': raise ValueError('Stato non completato')
        state = json.loads(Path(paths[0]).read_text())
        if parse(state['last_successful_end']) != parse(status['last_completed_at']):
            raise ValueError('Ricevuta di un altro intervallo')
        state.update(phase='pubblicato', publication_verified_at=stamp(utcnow()),
                     national_sha256=digest(paths[2]), status_sha256=digest(paths[1]), run_url=status.get('run_url'))
        write_atomic(paths[0], state)
    elif args.command == 'merge-state':
        remote_path, candidate_path, remote_log, candidate_log = map(Path, paths)
        state, events = merge_state(json.loads(remote_path.read_text()) if remote_path.exists() else {},
                                  json.loads(candidate_path.read_text()),
                                  json.loads(remote_log.read_text()) if remote_log.exists() else [],
                                  json.loads(candidate_log.read_text()))
        write_atomic(remote_path, state); write_atomic(remote_log, events)
    return 0


if __name__ == '__main__': sys.exit(main())
