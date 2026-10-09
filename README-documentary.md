# Revisioni documentali e conservazione delle evidenze

`data.json` resta l’unico catalogo autorevole. Il rapporto del primo lotto è in [docs/audit/2026-10-08/README.md](docs/audit/2026-10-08/README.md). I documenti in quella cartella sono evidenze di audit e code di lavoro, non archivi normativi alternativi.

Una scheda riesaminata può contenere `documentary_review`:

- `checked_at`: data reale di lettura della fonte, ISO `YYYY-MM-DD`.
- `scope`: informazioni effettivamente riscontrate.
- `outcome`: `verified` nel solo perimetro dichiarato, oppure `partial`, con limiti o attività residue.
- `legal_state`: `unverified`, `partial`, `in_force`, `amended`, `repealed`, `partially_repealed`, `replaced`, `adopted`, `consultation`, `uncertain_effectiveness`. Lo stato richiede l’evidenza pertinente; non è dedotto dalla risposta HTTP.
- `source_urls`: fonti istituzionali ufficiali effettivamente consultate.
- `claims`: oggetti con `aspect`, `source_url`, `locator`, `finding`. Gli aspetti ammessi sono `identity`, `content`, `version`, `status`, `territory`, `topics`, `approval`, `effectiveness`, `amendment`.
- `limitations`, `pending`: limiti e verifiche ancora necessarie.
- `record_version`: hash dell’oggetto e delle fonti della scheda e di `documentary_review.source_urls`, calcolato con `documentary.record_version(record)` **dopo** le correzioni, la normalizzazione dei topics e l’assegnazione della revisione con tutte le sue fonti. L’ordine delle fonti non modifica l’impronta.

L’impronta comprende tutti i campi della scheda, comprese relazioni, note, metadati completi dei documenti e future date di pubblicazione/efficacia. Esclude soltanto `id`, `checked`, `history`, `documentary_review` e `documentary_history`. La migrazione dell’algoritmo conserva integralmente le revisioni precedenti nella cronologia e non modifica la data di consultazione: non costituisce una nuova lettura né una conferma della vigenza.

Un esempio operativo di calcolo, usando il modulo esistente:

```python
import sys
sys.path.insert(0, 'scripts')
from documentary import record_version
record['documentary_review']['record_version'] = record_version(record)
```

Il calcolo dell’hash non costituisce un riesame. Se cambiano oggetto, stato, date normative, territorio, argomenti o fonti di una scheda già revisionata, leggere la fonte pertinente, conservare il precedente `documentary_review` in `documentary_history`, registrare i soli nuovi riscontri e poi calcolare la nuova versione. Conservare anche tutte le vecchie voci di `history`. Un semplice controllo URL o un nuovo workflow non aggiorna la data della lettura documentale.

Non dichiarare vigente/abrogato/sostituito/approvato/adottato un nuovo stato senza il riscontro specifico. Non confondere PDF originario, testo coordinato, allegati, cartografie e pagina del procedimento. Un timeout, una pagina di attesa, un HTTP 200 privo dell’atto o un errore temporaneo producono una limitazione; non provano assenza di modifiche. Per UNI usare il catalogo ufficiale e rispettare la licenza.

Il confronto preventivo con la base corrente richiede:

```sh
python scripts/topics.py normalize data.json
python scripts/topics.py validate data.json
python scripts/archive.py --base-ref origin/main
python -m unittest discover -s tests -v
node --check app.js
node tests/test_topic_filters.js
```

In caso di commit concorrente rileggere `main`, tassonomia e archivio, riapplicare solo i riscontri ancora validi e ripetere i controlli. Non ricreare `dist/`, non modificare i file nazionali o i checkpoint per un controllo territoriale/documentale. La validazione strutturale non sostituisce l’interpretazione dei documenti; le lacune delle schede legacy non modificate restano nella coda senza impedire aggiornamenti indipendenti dei registri automatici.

La chiave `review_source_urls` è riservata alla costruzione dell’impronta: la sua presenza nella scheda è rifiutata anche senza revisione, per impedire collisioni che nascondano metadati normativi. Le impronte esistenti restano invariate.

Lo stato `constitutionally_invalid` distingue una dichiarazione di illegittimità costituzionale dall’abrogazione legislativa. Richiede un riscontro di stato su una fonte ufficiale della pronuncia; non determina da solo la disciplina successiva o gli effetti sul singolo rapporto. Le evidenze precedenti restano nella cronologia.
