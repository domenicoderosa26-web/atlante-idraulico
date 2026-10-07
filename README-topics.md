# Tassonomia degli argomenti

La sorgente unica è `topic-taxonomy.json`: ordine delle categorie, etichette, alias, regole contestuali ed evidenze delle revisioni. Il frontend principale e la copia `dist` leggono questo stesso file; non si generano copie indipendenti.

## Audit del 7 ottobre 2026

Archivio principale: 102 schede, 28 vecchi tag. Copia storica `dist`: 68 schede. Non risultano altri importatori nel repository. `national.json` conserva metadati Normattiva, senza argomenti: i tag delle schede nazionali risiedono in `data.json`. La GitHub Action nazionale aggiorna i metadati, non acquisisce nuove schede. L’acquisizione territoriale è gestita dall’attività programmata esterna già esistente.

## Categorie canoniche

| Argomento | Schede principali al momento della migrazione |
|---|---:|
| Demanio e polizia idraulica | 3 |
| Attraversamenti e parallelismi | 6 |
| Drenaggio e acque meteoriche | 17 |
| Invarianza idraulica e idrologica | 8 |
| Prima pioggia | 20 |
| Scarichi e tutela delle acque | 30 |
| Risorse idriche e derivazioni | 12 |
| Riuso delle acque | 4 |
| CAM - Gestione sostenibile delle acque | 5 |
| PAI - Pericolosità e rischio idraulico | 19 |
| PAI - Pericolosità e rischio frane | 15 |
| PAI - Pericolosità e rischio geomorfologico | 2 |
| PGRA - Pericolosità alluvioni | 9 |
| PZP - Pericolosità e rischio | 9 |
| Misure di salvaguardia | 3 |
| Dissesto idrogeologico e stabilità dei versanti | 4 |
| Valanghe | 2 |
| Compatibilità idraulica | 20 |
| Bonifica e consorzi | 2 |
| Autorizzazioni ambientali | 1 |
| Pianificazione e gestione del rischio alluvioni | 4 |

Le categorie senza schede in una determinata copia dell’archivio non vengono mostrate nel relativo menu. L’ordine resta quello della tassonomia. Una raccolta che contiene effettivamente PAI e PGRA può possedere entrambi gli argomenti; questo non equivale ad attribuire PGRA a una variante PAI. Direttive e leggi quadro sul rischio alluvioni sono nella categoria separata “Pianificazione e gestione del rischio alluvioni”.

## Mapping completo dei vecchi argomenti

| Vecchio argomento | Nuovo argomento / criterio |
|---|---|
| Attraversamenti | Attraversamenti e parallelismi |
| Attraversamenti e parallelismi | Attraversamenti e parallelismi |
| Autorizzazioni | Autorizzazioni ambientali |
| Bonifica | Bonifica e consorzi |
| CAM | CAM - Gestione sostenibile delle acque |
| Compatibilità idraulica | Compatibilità idraulica |
| Consorzi di bonifica | Bonifica e consorzi |
| Demanio e polizia idraulica | Demanio e polizia idraulica |
| Derivazioni e risorsa idrica | Risorse idriche e derivazioni |
| Drenaggio | Drenaggio e acque meteoriche |
| Frane | Dissesto idrogeologico e stabilità dei versanti |
| Invarianza idraulica | Invarianza idraulica e idrologica |
| Misure di salvaguardia | Misure di salvaguardia |
| PAI | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico |
| PAI e PGRA | Compatibilità idraulica; PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio geomorfologico; PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni; Pianificazione e gestione del rischio alluvioni |
| PGRA | PGRA - Pericolosità alluvioni |
| PZP | PZP - Pericolosità e rischio |
| Pericolosità da alluvione | PGRA - Pericolosità alluvioni |
| Pericolosità da frana | PAI - Pericolosità e rischio frane |
| Pericolosità e rischio da frana | PAI - Pericolosità e rischio frane |
| Pericolosità e rischio idraulico | PAI - Pericolosità e rischio idraulico |
| Pericolosità idraulica | PAI - Pericolosità e rischio idraulico; PZP - Pericolosità e rischio |
| Prima pioggia | Prima pioggia |
| Risorse idriche | Risorse idriche e derivazioni |
| Riuso | Riuso delle acque |
| Scarichi e tutela acque | Scarichi e tutela delle acque |
| Valanghe | Valanghe |
| Variante cartografica | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |

Il mapping contestuale non si basa sul solo vecchio tag: usa l’oggetto dell’atto (titolo/riferimento/descrizione), i metadati di piano, i documenti e le fonti collegate. Le note e la cronologia possono citare altri piani e non sono usate per stabilire appartenenza. Le revisioni puntuali conservano fonte ed evidenza nella tassonomia; si applicano solo quando la fonte è ancora collegata alla scheda.

Sono rimossi il tag “Compatibilità idraulica” dalla variante PZP Campo Tures esclusivamente relativa a frane e i tag PAI/PGRA dal PGT Milano. Il TUA è incluso anche nel riuso, già descritto nel focus della scheda (artt. 98–99). Per Puglia il titolo III delle NTA usa la classificazione geomorfologica: non viene duplicata come PAI frane.

## Aggiornamenti e validazione

Prima di pubblicare un candidato territoriale:

```sh
python scripts/topics.py normalize data.json dist/data.json
python scripts/topics.py validate data.json dist/data.json
python -m unittest discover -s tests -v
node tests/test_topic_filters.js
```

Non sostituire la copia `dist` con l’archivio principale: normalizzare ogni file conservando i suoi contenuti. Il normalizzatore modifica solo `topics` e, quando necessario, i metadati `topic_classification`; tutti gli altri valori e la formattazione preesistente sono preservati. Nessun file viene scritto prima della validazione di tutti i candidati.

Se un tag resta ambiguo, la scheda è conservata con `topic_classification.status = "argomento da classificare"` e con gli alias irrisolti. Il comando li segnala su stderr. La scheda resta consultabile in “Tutti gli argomenti”, senza creare categorie arbitrarie. Se alcuni argomenti sono già validi restano disponibili. Una scheda senza argomenti e senza stato esplicito, oppure un argomento pubblico fuori tassonomia, blocca la validazione.

Per un piano non riconoscibile dai metadati disponibili, un revisore può aggiungere `topic_evidence`: oggetti con `category` (ID canonico), `source` (URL già collegato alla scheda) e `note` (evidenza verificata). Non aggiungere un piano soltanto perché citato per confronto, coordinamento o sostituzione. Le raccolte PAI/PGRA non revisionate restano da classificare, anziché essere mappate automaticamente in entrambi gli strumenti.

La Action nazionale valida gli argomenti prima dell’acquisizione Normattiva e nuovamente prima del push dopo il recupero di main; orari, retry, checkpoint, fonti e deploy non cambiano. `topics.yml` verifica gli archivi e i test a ogni push/PR pertinente. L’attività territoriale esistente deve usare gli stessi comandi prima di ogni commit, rileggendo main in caso di concorrenza. Il frontend accetta solo argomenti canonici e non popola il menu dai tag liberi.

La validazione sui push segnala una violazione anche per modifiche manuali. Non sono state introdotte regole di protezione del branch: il controllo precommit dell’importatore e la validazione nel frontend sono distinti dal controllo CI successivo al push.

## Verifiche

20 test Python (compresi i 9 esistenti), test JavaScript sui filtri reali di entrambe le copie, validazione dei JSON/YAML e controllo della sintassi JavaScript. Simulato un nuovo atto PAI idraulico con vecchi alias e un controllo Normattiva senza modifiche. Verificati casi PAI frane/idraulico/geomorfologico, PGRA, PZP, alias, multitag, categorie duplicate, import ambiguo e dati invalidi. La migrazione non cambia il numero delle schede né gli altri campi degli archivi. Nessuna scheda esistente resta da classificare.
