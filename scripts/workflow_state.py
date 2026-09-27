"""Validate the public result and decide whether a scheduled fallback is needed."""
import datetime as dt
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
from normattiva import parse, validate


def already_complete(path, now=None):
    file = Path(path)
    if not file.exists():
        return False
    state = json.loads(file.read_text())
    if not isinstance(state, dict) or 'last_successful_end' not in state:
        raise ValueError('Checkpoint non valido')
    today = (now or dt.datetime.now(dt.timezone.utc)).astimezone(ZoneInfo('Europe/Rome')).date()
    return parse(state['last_successful_end']).astimezone(ZoneInfo('Europe/Rome')).date() == today


def check(paths):
    national, data, status, checkpoint = [json.loads(Path(path).read_text()) for path in paths]
    validate(national, data['records'])
    if status['outcome'] != 'completato' or status['timezone'] != 'Europe/Rome':
        raise ValueError('Stato pubblico non valido')
    if not isinstance(status['changes_detected'], int) or status['changes_detected'] < 0:
        raise ValueError('Conteggio modifiche non valido')
    if parse(checkpoint['last_successful_end']) != parse(status['last_completed_at']):
        raise ValueError('Checkpoint e stato pubblico discordanti')


def validate_state(path):
    file = Path(path)
    if not file.exists():
        return
    state = json.loads(file.read_text())
    if not isinstance(state, dict) or 'last_successful_end' not in state:
        raise ValueError('Checkpoint non valido')
    parse(state['last_successful_end'])


if __name__ == '__main__':
    if sys.argv[1] == 'validate-state':
        validate_state(sys.argv[2])
        raise SystemExit(0)
    if sys.argv[1] == 'already-complete':
        raise SystemExit(0 if already_complete(sys.argv[2]) else 1)
    if sys.argv[1] == 'validate':
        check(sys.argv[2:])
