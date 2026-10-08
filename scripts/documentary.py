"""Structural evidence checks; these do not establish legal validity."""
import datetime as dt
import hashlib
import json
import re
from urllib.parse import urlsplit

ASPECTS = {'identity', 'content', 'version', 'status', 'territory', 'topics',
           'approval', 'effectiveness', 'amendment'}
STATES = {'unverified', 'partial', 'in_force', 'amended', 'repealed',
          'partially_repealed', 'replaced', 'adopted', 'consultation',
          'uncertain_effectiveness'}
ASSERTION = re.compile(r'\b(vigente|in vigore|abrogat\w*|sostituit\w*|'
                       r'approvat\w*|adottat\w*|efficace)\b', re.I)


def record_version(record):
    """Bind a review to its object and sources, excluding execution timestamps."""
    # Protect all normative metadata, including relations, document labels,
    # publication/effectiveness dates and fields introduced in future records.
    # Execution logs and the evidence itself are excluded to avoid circularity.
    excluded = {'id', 'checked', 'history', 'documentary_review', 'documentary_history'}
    value = {key: item for key, item in record.items() if key not in excluded}
    review = record.get('documentary_review', {})
    sources = review.get('source_urls', []) if isinstance(review, dict) else []
    value['review_source_urls'] = sorted(sources) if isinstance(sources, list) and all(
        isinstance(source, str) for source in sources) else sources
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_review(record, baseline=None, today=None):
    label = record['id'] + ': revisione documentale: '
    review = record.get('documentary_review')
    # Legacy records remain usable. Evidence is required when a new/changed
    # status makes a positive legal assertion, not for unrelated daily logs.
    if baseline is not None and record.get('status') != baseline.get('status'):
        if ASSERTION.search(record.get('status', '')):
            require(review is not None, label + 'nuovo stato senza evidenza')
    if review is None:
        require(not record.get('documentary_history'), label + 'revisione corrente mancante')
        if baseline and baseline.get('documentary_review'):
            raise ValueError(label + 'evidenza precedente rimossa')
        return
    require(isinstance(review, dict), label + 'oggetto non valido')
    try:
        checked = dt.date.fromisoformat(review['checked_at'])
    except (KeyError, TypeError, ValueError):
        raise ValueError(label + 'data non valida')
    require(checked <= (today or dt.date.today()), label + 'data futura')
    date = record.get('date', '')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        require(checked >= dt.date.fromisoformat(date), label + 'verifica precedente all’atto')
    require(review.get('record_version') == record_version(record), label + 'contenuto cambiato: riesaminare la fonte')
    require(isinstance(review.get('scope'), str) and review['scope'].strip(), label + 'perimetro mancante')
    require(review.get('outcome') in {'partial', 'verified'}, label + 'esito non valido')
    for field in ['limitations', 'pending']:
        require(isinstance(review.get(field), list) and all(isinstance(v, str) and v.strip()
                for v in review[field]), label + field + ' non valido')
    if review['outcome'] == 'partial':
        require(review['limitations'] or review['pending'], label + 'verifica parziale senza limiti')
    sources = review.get('source_urls')
    require(isinstance(sources, list) and sources, label + 'fonti mancanti')
    for source in sources:
        require(isinstance(source, str), label + 'fonte non testuale')
        url = urlsplit(source)
        require(url.scheme == 'https' and bool(url.hostname), label + 'fonte HTTPS non valida')
    claims = review.get('claims')
    require(isinstance(claims, list) and claims, label + 'riscontri mancanti')
    for claim in claims:
        require(isinstance(claim, dict) and claim.get('aspect') in ASPECTS,
                label + 'aspetto non valido')
        require(claim.get('source_url') in sources, label + 'riscontro senza fonte associata')
        require(all(isinstance(claim.get(k), str) and claim[k].strip()
                    for k in ['locator', 'finding']), label + 'riscontro privo di evidenza puntuale')
    if baseline is not None and record.get('status') != baseline.get('status'):
        if ASSERTION.search(record.get('status', '')):
            require(any(c['aspect'] in {'status', 'approval', 'effectiveness', 'amendment'}
                        for c in claims), label + 'nuovo stato senza riscontro specifico')
    state = review.get('legal_state')
    require(state in STATES, label + 'stato strutturato non valido')
    if state in {'in_force', 'amended', 'repealed', 'partially_repealed', 'replaced'}:
        require(any(c['aspect'] in {'status', 'effectiveness', 'amendment'} for c in claims),
                label + 'stato giuridico senza riscontro specifico')
    if state == 'adopted':
        require(any(c['aspect'] == 'approval' for c in claims), label + 'adozione senza atto')
    # Earlier evidence is content-bound and must survive a new review.
    history = record.get('documentary_history', [])
    require(isinstance(history, list) and all(isinstance(h, dict) for h in history),
            label + 'cronologia non valida')
    if baseline and baseline.get('documentary_review'):
        old = baseline['documentary_review']
        require(old == review or old in history, label + 'revisione precedente non conservata')
        require(checked >= dt.date.fromisoformat(old['checked_at']), label + 'data precedente alla base')
    if baseline:
        require(all(h in history for h in baseline.get('documentary_history', [])),
                label + 'cronologia precedente non conservata')
