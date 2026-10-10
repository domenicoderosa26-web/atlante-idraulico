# Pre-verifica tecnica della Fase 3

Questa infrastruttura riserva Work alla lettura e al coordinamento normativo. Non avvia un nuovo audit: prepara piccoli gruppi dalla coda residua indicata da `docs/audit/progress.json`. Non usa API AI, dipendenze Python esterne o runner dedicati.

## Esecuzione e limiti

Il workflow `Pre-verifica tecnica Fase 3` esegue i test sulle PR e prepara evidenze su `main` ogni lunedì e giovedì alle 05:41 UTC (07:41 in estate, 06:41 in inverno a Roma), oppure su richiesta. Il limite ordinario è tre attività e otto richieste per esecuzione. La selezione favorisce `next_batch` per le attività mai preparate, poi quelle preparate meno recentemente; usa ID unici e impronte di scheda, operazioni e fonti. Le attività già preparate vengono riaperte tecnicamente se cambiano o scadono le ricevute. Un lotto che esaurisce il budget resta incompleto e prosegue nelle esecuzioni successive, riusando gli URL già controllati.

```sh
python scripts/precheck.py --plan
python scripts/precheck.py --batch-size 3 --max-requests 8
python -m unittest discover -s tests -v
```

`--plan` non effettua richieste e non scrive file; gli esiti simulati non sono evidenze da pubblicare. Le ricevute del completamento già acquisito sono riusate per sette giorni dopo un accesso riuscito; errori, blocchi e challenge hanno un intervallo minimo di un giorno. Nuovi URL richiedono un controllo. Il riuso è tecnico e non prolunga la validità di una revisione normativa.

Le richieste HTTPS sono sequenziali, distanziate di due secondi, con timeout di 12 secondi, lettura massima di 2 MB e durata del job limitata a dieci minuti. Non vengono scaricati allegati scoperti nei siti né eseguiti crawling, OCR o letture normative. Gli host autorizzati sono esplicitamente elencati in `scripts/precheck-hosts.json`, ricavati dalle fonti istituzionali già citate. Ogni nuovo host e redirect richiede un'aggiunta revisionata alla lista. Servizi delegati e cataloghi commerciali, incluso UNI, restano disponibili per l'accesso manuale dalla coda. Non si aggirano autenticazioni o challenge.

## Evidenze nello stesso registro

L'unica destinazione persistente è `technical_precheck` dentro `docs/audit/progress.json`. Le sezioni precedenti del registro rimangono identiche. L'estensione contiene:

- `selected`, `requests`, `tasks`: lotto, budget consumato e versioni preparate; non sono stati giuridici.
- `seed_receipts`: riferimento alle ricevute esistenti, senza copiarle in un nuovo archivio.
- `receipts`: sole nuove osservazioni o ricontrolli pertinenti alla coda. URL, data, stato HTTP, destinazione, tipo, firma PDF, titolo HTML candidato, dimensione letta, impronta e validator HTTP sono verificabili; non si conservano i corpi dei documenti.
- `normative_queue`: attività residue, priorità tecnica motivata, fonti, disponibilità dei documenti, scadenza del controllo, limiti e riferimento alle evidenze sostanziali già acquisite. La lista deriva dalla coda esistente e non certifica una ricognizione esaustiva.

La firma `%PDF-` identifica solo il formato. Il titolo HTML è un indizio di identità e può riferirsi alla pagina del procedimento. Un URL censito come PDF che restituisce HTML non viene indicato come PDF disponibile. Il testo del PDF, cartografie, allegati e identità dell'atto devono ancora essere esaminati. Le impronte complete e quelle di un prefisso sono separate: l'uguaglianza di un prefisso non esclude modifiche nel resto del documento. Per variazioni confrontabili si conserva anche l'impronta dell'osservazione precedente; gli audit originali restano immutati.

I validator ETag/Last-Modified sono usati solo per rappresentazioni complete già osservate. Un 304 riusa quell'osservazione, senza dichiarare vigente o verificato l'atto. Timeout, HTTP non riusciti, corpi vuoti, challenge, formati discordanti e URL non autorizzati non chiudono attività normative e non interrompono gli altri controlli. Le priorità `high`/`normal` misurano la preparazione tecnica, non l'importanza o la validità giuridica.

## Pubblicazione e conservazione

La serializzazione impedisce due esecuzioni concorrenti di questa automazione. Il workflow verifica che solo l'estensione tecnica sia cambiata, esegue il controllo di conservazione dell'archivio e pubblica esclusivamente `docs/audit/progress.json`. Il push è ordinario: se un altro processo aggiorna `main`, fallisce senza sovrascrivere nulla; rieseguire il workflow sulla nuova base. I limiti valgono anche in caso di errore e non sono aumentati da retry automatici nello stesso job.

Dopo il push viene usata la funzione esistente `workflow_state.verify_files` per confrontare tutti i byte del registro pubblico su GitHub Pages con il risultato locale. Se Pages non si aggiorna, il job fallisce e non dichiara pubblicazione verificata. Il controllo può richiedere una build Pages usando il token standard di GitHub Actions; non cambia la configurazione del sito. I log di Actions riportano il lotto e l'esito della pubblicazione senza nuovi archivi di artifact.

Normattiva, automazione territoriale, supervisione, frontend, catalogo `data.json`, cronologie e stati giuridici non sono modificati. La verifica normativa sostanziale e la pubblicazione delle relative modifiche seguono i controlli esistenti. La Fase 3 resta aperta finché le attività sostanziali non vengono risolte.
