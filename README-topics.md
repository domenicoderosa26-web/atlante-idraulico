# Argomenti: tassonomia definitiva e verifica completa

Revisione aggiornata all’8 ottobre 2026. La sorgente unica è `topic-taxonomy.json`, versione 2: contiene **esattamente 14 argomenti autorizzati**, le regole di ingresso e le evidenze delle riclassificazioni. Non contiene altre categorie attive o sottocategorie. Gli alias precedenti servono soltanto a riconoscere un ingresso legacy; non vengono pubblicati come valori di `topics`.

## Esito della riclassificazione

- **106 schede uniche controllate** nel catalogo pubblico, comprese 18 nazionali; nessuna cancellata o duplicata. Le quattro aggiunte dell’8 ottobre sono revisionate con fonte, evidenza e versione dell’oggetto.
- **72 schede con associazioni/denominazioni cambiate**; altre 5 hanno soltanto ricevuto l’ordine A–Z dei tag. Tutte le 102 schede originarie sono riesaminate; le 30 associazioni già pertinenti restano valide.
- **33 schede multiargomento** dopo la revisione. Le associazioni multiple seguono materie sostanziali, non rinvii marginali.
- **0 schede prive di argomenti**, **0 schede da classificare**, **0 valori attivi fuori tassonomia**.
- La copia storica `dist/data.json` (68 schede, tutte già comprese nelle 106 identità principali) è stata rimossa nel consolidamento dell’8 ottobre: il catalogo autorevole è soltanto `data.json`. La copia precedente resta nella cronologia Git.
- `national.json` conserva 18 metadati di atti già presenti nel catalogo e non contiene argomenti; non aggiunge altre norme al conteggio.

Titoli, descrizioni, focus, fonti, URL, PDF, date, territori, livelli e tutti gli altri valori e byte degli archivi sono invariati. I file HTML cambiano soltanto nel parametro di versione dello script per rendere subito effettiva la nuova logica; nessuna modifica alla grafica.

## Le 14 categorie

Il menu mostra **tutte e sole le 14 categorie**, anche se una copia dell’archivio non contiene schede per una voce. `topicCategories()` ordina a ogni rendering una copia della tassonomia con `localeCompare(..., 'it', {sensitivity:'base'})`: l’ordine visualizzato non dipende dall’ordine del JSON. I badge e i filtri rapidi utilizzano le stesse etichette.

| Argomento (A–Z) | Schede principali |
|---|---:|
| Attraversamenti e parallelismi | 6 |
| Autorizzazioni ambientali | 1 |
| Bonifica e consorzi | 2 |
| Demanio e polizia idraulica | 5 |
| Invarianza idraulica e idrologica | 8 |
| PAI - Pericolosità e rischio frane | 21 |
| PAI - Pericolosità e rischio geomorfologico | 2 |
| PAI - Pericolosità e rischio idraulico | 21 |
| PGRA - Pericolosità alluvioni | 14 |
| PZP - Pericolosità e rischio idraulico | 5 |
| Riuso delle acque meteoriche | 3 |
| Scarichi e tutela delle acque | 30 |
| Smaltimento acque meteoriche e reflue | 11 |
| Trattamento acque di prima pioggia | 18 |

## Vecchie categorie eliminate

Sono rimossi come valori attivi tutti gli 11 nomi precedenti non ammessi:

- CAM - Gestione sostenibile delle acque
- Compatibilità idraulica
- Dissesto idrogeologico e stabilità dei versanti
- Drenaggio e acque meteoriche
- Misure di salvaguardia
- PZP - Pericolosità e rischio
- Pianificazione e gestione del rischio alluvioni
- Prima pioggia
- Risorse idriche e derivazioni
- Riuso delle acque
- Valanghe

Le parole tecniche possono restare nei titoli, focus o cronologie, che non sono stati riscritti. Le vecchie denominazioni compaiono soltanto nella documentazione e negli alias di ingresso: la ricerca nel repository ha verificato che non popolino menu, badge, risultati o statistiche come argomenti autonomi.

## Casi limite e criteri adottati

| Caso | Decisione motivata |
|---|---|
| Invarianza regionale e linee guida art. 47 PAI Sardegna | Unica voce invarianza: volumi, compensazioni e controllo dei deflussi sono il tema specifico. Eliminati i tag generici compatibilità/drenaggio e, per la linea guida, la duplicazione PAI idraulico. |
| D.Lgs. 49/2010 e direttiva Alluvioni | PGRA come tema sostanziale di mappe e pianificazione del rischio alluvionale. Restano leggi/direttive nel campo tipo, non diventano atti di piano. |
| Toscana L.R. 41/2018 | PGRA per gestione del rischio alluvionale e demanio per tutela dei corsi d’acqua. |
| PAI Puglia e Sicilia | Idraulico e geomorfologico dove le NTA distinguono tali componenti; nessuna duplicazione automatica con frane. |
| PZP Campo Tures, Nova Ponente (776 e 741), Rasun-Anterselva | Voce ammessa frane/fenomeni gravitativi, applicata per tema prevalente anche se l’etichetta contiene PAI. Sono ancora strumenti PZP, come dichiarano titolo, riferimenti e fonti; non sono nel filtro PZP idraulico. Rasun comprende anche valanghe. |
| PZP Sarentino | PZP idraulico + frane/fenomeni gravitativi per le componenti idraulica e valanghiva; nessun filtro valanghe. |
| PZP Badia, Fortezza, La Valle e regolamento provinciale | PZP idraulico; conservata l’appartenenza effettiva alla componente idraulica. |
| Riuso refluo: D.M. 185/2003 e regolamenti UE 2020/741 e 2024/1765 | Scarichi e tutela delle acque: requisiti qualitativi delle acque reflue/affinate. Non assegnati al riuso meteorico. |
| CAM edilizia 2025, CAM verde e D.P.P. Bolzano 6/2008 | Riuso meteorico dove esplicito, insieme alle altre materie sostanziali. CAM edilizia §§ 2.3.14–2.3.15: reti separate e raccolta/trattamento/stoccaggio/riuso. |
| CAM Strade e relativo correttivo | Smaltimento: drenaggi lineari e tubazioni. Eliminata l’associazione prima pioggia non comprovata dal focus specifico. |
| D.Lgs. 36/2023 art. 57 | Caso di raccordo generale: smaltimento per l’obbligo CAM negli affidamenti di reti/drenaggi. È una collocazione tematica nella voce più vicina, non una prescrizione tecnica di smaltimento o un’autorizzazione ambientale. |
| TUA | Smaltimento (art. 100), scarichi/tutela, prima pioggia (art. 113) e pertinenze idriche (art. 115). Nessun riuso meteorico desunto dal solo riuso generale e nessun tag di piano dal rinvio generale alla pianificazione. |
| NTC, D.M. attraversamenti e art. 25 Codice della strada | Attraversamenti; rimossi gli argomenti generici drenaggio/risorse che non esprimono il focus sostanziale. |
| L.R. Basilicata 9/2017 | Scarichi/tutela; la prima pioggia appartiene alle linee guida attuative specifiche, non al semplice rinvio dell’atto quadro. |

Fonti di approfondimento per questa revisione: testo coordinato [L.R. Toscana 41/2018](https://raccoltanormativa.consiglio.regione.toscana.it/articolo?urndoc=urn:nir:regione.toscana:legge:2018-07-24;41), [Allegato 1 CAM edilizia MASE riprodotto dall’ANCE](https://ance.it/wp-content/uploads/allegati/allegato_1_cam_edilizia_30_10_25-def.pdf), [scheda istituzionale CAM Verde della Regione Sardegna](https://portal.sardegnasira.it/documents/21213/583397/12.%2BScheda%2BOperativa%2B-%2BCAM%2BVerde%2Bpubblico%2B%28DM%2B10%2Bmarzo%2B2020%29.pdf/35d3b5c5-bc25-4df8-bd8e-1f2df0ad9860). Le fonti originali delle schede restano invariate.

## Aggiornamenti futuri e blocchi di pubblicazione

Prima di ogni pubblicazione:

```sh
python scripts/topics.py normalize data.json
python scripts/topics.py validate data.json
python scripts/archive.py --base-ref origin/main
python -m unittest discover -s tests -v
node tests/test_topic_filters.js
```

Il normalizzatore applica revisioni complete legate alla fonte e all’oggetto (titolo, riferimento, descrizione e focus). Se tali campi cambiano, la vecchia revisione non viene applicata automaticamente. Nuovi casi chiari sono riconosciuti dalle regole sul loro oggetto; note e cronologie non costituiscono evidenza di piano. Una revisione manuale o `topic_evidence` deve avere URL già collegato alla scheda ed evidenza verificata.

Un candidato ambiguo/ignoto **blocca la normalizzazione e la pubblicazione** senza scrivere alcun archivio: tutti i candidati sono verificati prima dei salvataggi. `topic_classification` è soltanto una diagnosi in memoria, non una categoria o stato pubblicabile. Nessuna norma può essere pubblicata senza almeno un argomento ammesso; non sono introdotti argomenti di ripiego. Il frontend rifiuta categorie estranee, schede senza argomenti, tag duplicati, ID duplicati e candidati da classificare.

La Action nazionale mantiene la validazione prima dell’acquisizione e prima del push. La Action argomenti esegue validazione e test su push/PR. L’attività territoriale esistente legge la stessa tassonomia e applica i controlli prima del commit, rileggendo main in caso di concorrenza. Orari e fonti di monitoraggio restano invariati. Le verifiche CI successive a push non equivalgono a una protezione preventiva del branch; non sono state introdotte regole di branch protection.

## Verifiche riproducibili

27 test Python, compresi i 9 test originali. Il test JavaScript esegue il codice reale del frontend principale e verifica tutte le 14 voci, ordine A–Z con tassonomia deliberatamente invertita, 168 combinazioni argomento/territorio/livello sul catalogo autorevole, ricerca combinata, ordinamento per titolo/data, conteggi e unicità delle schede multiargomento. Verificata anche una simulazione di import giornaliero e un controllo nazionale senza modifiche.

## Archivio autorevole e pubblicazione

GitHub Pages pubblica `main/(root)`: il job di build esegue il checkout di `main` e carica l’intera radice come artifact. `app.js` legge `data.json` dalla stessa directory, insieme alla tassonomia e ai registri nazionali facoltativi. Non esiste un processo di compilazione verso `dist/`.

La cartella `dist/` proveniva dal caricamento del 18 settembre e conservava 68 schede, contro le 106 nella radice all’8 ottobre. Gli aggiornamenti territoriali scrivono soltanto l’archivio principale; quelli nazionali scrivono `national.json` e `update-status.json`. La cartella storica, inclusa anch’essa nell’artifact Pages, rendeva accessibile una seconda distribuzione obsoleta. È rimossa con i suoi duplicati frontend e PDF; i PDF identici nella radice restano intatti. Il vecchio percorso `/dist/` non è più una destinazione pubblicata; la cronologia Git conserva i file precedenti.

`scripts/archive.py` verifica struttura, ID unici, relazioni, rimandi territoriali, sintassi degli URL HTTPS, tassonomia e registro nazionale. Rifiuta la ricomparsa di `dist/`. Con `--base-ref` impedisce la perdita di ID e il ritorno a un’edizione precedente, senza bloccare aggiunte o aggiornamenti documentati delle schede. La CI confronta con la base della PR o con il commit precedente del push. Il workflow nazionale verifica anche la base appena riletta prima del push, mantenendo il meccanismo di concorrenza esistente. Il controllo territoriale deve rileggere `main` e ripetere questi controlli prima del commit. Non sono cambiati orari, fonti, checkpoint o logiche di monitoraggio.

Il test JavaScript verifica anche il percorso reale di caricamento: file nella radice, registro nazionale facoltativo e conservazione del catalogo già caricato se il successivo caricamento fallisce. La validazione degli URL è strutturale: non sostituisce le verifiche di raggiungibilità e vigenza delle fonti. La CI su push segnala gli errori, ma non introduce una nuova protezione del branch o un diverso processo Pages.

## Registro completo delle 106 schede riesaminate

Le evidenze puntuali e le fonti sono in `reviewed_records` della tassonomia; questa tabella permette di controllare le associazioni finali senza ricostruire la migrazione.

| ID | Riferimento | Argomenti finali |
|---|---|---|
| rd523 | R.D. 523/1904 | Attraversamenti e parallelismi; Demanio e polizia idraulica |
| rd1775 | R.D. 1775/1933 | Demanio e polizia idraulica |
| rd368 | R.D. 368/1904 | Bonifica e consorzi; Demanio e polizia idraulica |
| rd215 | R.D. 215/1933 | Bonifica e consorzi |
| dl152 | D.Lgs. 152/2006 | Demanio e polizia idraulica; Scarichi e tutela delle acque; Smaltimento acque meteoriche e reflue; Trattamento acque di prima pioggia |
| dl49 | D.Lgs. 49/2010 | PGRA - Pericolosità alluvioni |
| ntc18 | D.M. 17/01/2018 | Attraversamenti e parallelismi |
| ue60 | Direttiva 2000/60/CE | Scarichi e tutela delle acque |
| ueall | Direttiva 2007/60/CE | PGRA - Pericolosità alluvioni |
| lom7 | R.R. 7/2017 | Invarianza idraulica e idrologica |
| sic102 | D.D.G. 102/2021 | Invarianza idraulica e idrologica |
| ven2948 | D.G.R. 2948/2009 | Invarianza idraulica e idrologica |
| fvg83 | D.P.Reg. 083/Pres/2018 | Invarianza idraulica e idrologica |
| pug26 | R.R. 26/2013 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| pie1 | R.R. 1/R/2006 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| lig4 | R.R. 4/2009 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| er286 | D.G.R. 286/2005 | Trattamento acque di prima pioggia |
| er1860 | D.G.R. 1860/2006 | Trattamento acque di prima pioggia |
| tos41 | L.R. 41/2018 | Demanio e polizia idraulica; PGRA - Pericolosità alluvioni |
| mar53 | L.R. 19/2023, art. 31 · D.G.R. 53/2014 | Invarianza idraulica e idrologica |
| laz18 | D.C.R. 18/2018 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| abr17 | L.R. 17/2008 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| cal10 | L.R. 10/1997 | Scarichi e tutela delle acque |
| umb627 | D.G.R. 627/2019 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| mol25 | D.C.R. 25/2018 | Scarichi e tutela delle acque |
| vda2030 | PTA 2030 | Scarichi e tutela delle acque |
| ligpta | PTA Liguria | Scarichi e tutela delle acque |
| bz6 | D.P.P. Bolzano 6/2008 | Riuso delle acque meteoriche; Scarichi e tutela delle acque; Smaltimento acque meteoriche e reflue; Trattamento acque di prima pioggia |
| bz23 | D.P.P. 23/2019 | PZP - Pericolosità e rischio idraulico |
| tnpta | PTA 2022–2027 | Scarichi e tutela delle acque |
| bzpta | L.P. Bolzano 8/2002 | Scarichi e tutela delle acque |
| bari | Città metropolitana di Bari | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| milano | PGT Milano | Invarianza idraulica e idrologica |
| venezia | Regolamento edilizio · Venezia | Scarichi e tutela delle acque; Smaltimento acque meteoriche e reflue |
| aprilia | Comune di Aprilia | Scarichi e tutela delle acque |
| medicina | Comune di Medicina | Scarichi e tutela delle acque |
| uni752 | UNI EN 752:2017 | Smaltimento acque meteoriche e reflue |
| uni12056 | UNI EN 12056-3:2001 | Smaltimento acque meteoriche e reflue |
| uni858 | UNI EN 858-2:2004 | Trattamento acque di prima pioggia |
| dist-po | PAI / PGRA · Fiume Po | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |
| po-pai-estensione-13-2025 | Del. CIP 13/2025 · progetto di variante PAI Po | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico |
| dist-alpi | PAI / PGRA · Alpi Orientali | PGRA - Pericolosità alluvioni |
| dist-sett | PAI / PGRA · Appennino Settentrionale | PGRA - Pericolosità alluvioni |
| dist-centr | PAI / PGRA · Appennino Centrale | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |
| bas9 | L.R. Basilicata 9/2017 | Scarichi e tutela delle acque |
| bas471 | D.G.R. Basilicata 471/2026 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| dist-merid | PAI / PGRA · Appennino Meridionale | PGRA - Pericolosità alluvioni |
| dist-sard | PAI / PGRA · Sardegna | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |
| sar-pai-frane-42-2026 | D.P.Reg. Sardegna 42/2026 · variante PAI–frane | PAI - Pericolosità e rischio frane |
| sar-pai-barrali-162-2026 | Det. SG Sardegna 162/2026 · variante PAI Barrali | PAI - Pericolosità e rischio idraulico |
| dist-sici | PAI / PGRA · Sicilia | PAI - Pericolosità e rischio geomorfologico; PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |
| sic-pgra3-02-2026 | Del. CIP Sicilia 2/2026 · PGRA III ciclo | PGRA - Pericolosità alluvioni |
| dmattr2014 | D.M. 04/04/2014 | Attraversamenti e parallelismi |
| camed2025 | D.M. 24/11/2025 | Riuso delle acque meteoriche; Smaltimento acque meteoriche e reflue |
| camstrade2024 | D.M. 05/08/2024 · CAM Strade | Smaltimento acque meteoriche e reflue |
| camverde2020 | D.M. 10/03/2020 · CAM Verde | Riuso delle acque meteoriche; Smaltimento acque meteoriche e reflue |
| appalti36 | D.Lgs. 36/2023 · art. 57 | Smaltimento acque meteoriche e reflue |
| camstrade2025 | D.M. 11/09/2025 · correttivo CAM Strade | Smaltimento acque meteoriche e reflue |
| pai-calabria2001 | PAI Calabria · NAMS aggiornate 2011 | PAI - Pericolosità e rischio idraulico |
| pai-calabria-lao | PSdGDAM-RisAl-Cal/L | PAI - Pericolosità e rischio idraulico |
| pai-basilicata | PAI ex AdB Basilicata | PAI - Pericolosità e rischio frane; PAI - Pericolosità e rischio idraulico |
| pai-lgv | PSAI Liri–Garigliano · rischio idraulico | PAI - Pericolosità e rischio idraulico |
| pai-puglia | PAI Puglia e Ofanto | PAI - Pericolosità e rischio geomorfologico; PAI - Pericolosità e rischio idraulico |
| pai-campania | PAI Campania Centrale | PAI - Pericolosità e rischio idraulico |
| pai-biferno-e-minori | PAI Biferno e minori | PAI - Pericolosità e rischio idraulico |
| pai-trigno | PAI Trigno | PAI - Pericolosità e rischio idraulico |
| pai-fortore | PAI Fortore | PAI - Pericolosità e rischio idraulico |
| laz117 | D.G.R. Lazio 117/2020 | Invarianza idraulica e idrologica |
| sar-inv-2017 | Del. C.I. 2/2017 · art. 47 NTA PAI | Invarianza idraulica e idrologica |
| lom4pp | R.R. Lombardia 4/2006 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| sar6925 | D.G.R. Sardegna 69/25 del 10/12/2008 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| tos20 | L.R. Toscana 20/2006 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| tos46 | D.P.G.R. Toscana 46/R/2008 | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| venpta39 | PTA Veneto · art. 39 NTA | Scarichi e tutela delle acque; Trattamento acque di prima pioggia |
| dpr753 | D.P.R. 753/1980 | Attraversamenti e parallelismi |
| codstrada285 | D.Lgs. 285/1992 · art. 25 | Attraversamenti e parallelismi |
| dpr495 | D.P.R. 495/1992 · artt. 65–69 | Attraversamenti e parallelismi; Smaltimento acque meteoriche e reflue |
| dm185 | D.M. 185/2003 | Scarichi e tutela delle acque |
| dpr59 | D.P.R. 59/2013 | Autorizzazioni ambientali; Scarichi e tutela delle acque |
| ue741reuse | Reg. (UE) 2020/741 | Scarichi e tutela delle acque |
| ue1765reuse | Reg. delegato (UE) 2024/1765 | Scarichi e tutela delle acque |
| bz-badia-pzp-782-2026 | D.G.P. Bolzano 782/2026 | PZP - Pericolosità e rischio idraulico |
| bz-campo-tures-pzp-799-2026 | D.G.P. Bolzano 799/2026 | PAI - Pericolosità e rischio frane |
| bz-nova-ponente-pzp-776-2026 | D.G.P. Bolzano 776/2026 | PAI - Pericolosità e rischio frane |
| bz-fortezza-pzp-742-2026 | D.G.P. Bolzano 742/2026 | PZP - Pericolosità e rischio idraulico |
| bz-nova-ponente-pzp-741-2026 | D.G.P. Bolzano 741/2026 | PAI - Pericolosità e rischio frane |
| bz-sarentino-pzp-740-2026 | D.G.P. Bolzano 740/2026 | PAI - Pericolosità e rischio frane; PZP - Pericolosità e rischio idraulico |
| bz-la-valle-pzp-739-2026 | D.G.P. Bolzano 739/2026 | PZP - Pericolosità e rischio idraulico |
| bz-rasun-anterselva-pzp-738-2026 | D.G.P. Bolzano 738/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-idraulico-67-2026 | Del. CIP AUBAC 67/2026 | PAI - Pericolosità e rischio idraulico |
| centr-pai-frane-68-2026 | Del. CIP AUBAC 68/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-nestore-139-2026 | D.S. AUBAC 139/2026 | PAI - Pericolosità e rischio idraulico |
| sett-pgra-variante-62-2026 | Del. CIP 62/2026 · Appennino Settentrionale | PGRA - Pericolosità alluvioni |
| centr-pai-lettomanoppello-142-2026 | D.S. AUBAC 142/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-notaresco-143-2026 | D.S. AUBAC 143/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-notaresco-144-2026 | D.S. AUBAC 144/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-notaresco-145-2026 | D.S. AUBAC 145/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-pescara-146-2026 | D.S. AUBAC 146/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-spoltore-147-2026 | D.S. AUBAC 147/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-penne-148-2026 | D.S. AUBAC 148/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-tronto-140-2026 | D.S. AUBAC 140/2026 | PAI - Pericolosità e rischio idraulico |
| centr-pai-offida-39-2026 | D.S. AUBAC 39/2026 | PAI - Pericolosità e rischio frane |
| centr-pai-fosso-secco-20-2026 | D.S. AUBAC 20/2026 | PAI - Pericolosità e rischio idraulico |
| centr-pai-vigna-corte-123-2026 | D.S. AUBAC 123/2026 | PAI - Pericolosità e rischio frane |
| po-pai-pgra-terdoppio-5-2026 | D.S. AdB Po 5/2026 · progetto Terdoppio | PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |
| po-pai-pgra-mera-27-2026 | D.S. AdB Po 27/2026 · progetto Mera | PAI - Pericolosità e rischio idraulico; PGRA - Pericolosità alluvioni |
