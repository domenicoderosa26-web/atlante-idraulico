# Monitoraggio Normattiva degli atti nazionali

Il sito usa `data.json` per il catalogo esistente e `national.json` come registro supplementare delle 18 schede nazionali. La lettura di quest'ultimo è facoltativa: se non risponde, il catalogo resta utilizzabile. L'aggiornamento territoriale esterno continua a lavorare su `data.json`.

## Fonte e limiti

Le API ufficiali sono documentate da Normattiva in <https://dati.normattiva.it/assets/come_fare_per/API_Normattiva_OpenData.pdf>. Ambiente di produzione: `https://api.normattiva.it/t/normattiva.api`. `POST /bff-opendata/v1/api/v1/ricerca/aggiornati` segnala gli atti aggiornati; `POST /bff-opendata/v1/api/v1/atto/dettaglio-atto-urn` verifica identità e metadati. `POST /bff-opendata/v1/api/v1/ricerca/avanzata` interroga le classi ufficiali 1 (senza aggiornamenti), 2 (aggiornato), 3 (abrogato) con estremi e codice redazionale. Una classificazione ambigua non cambia i dati pubblicati e viene registrata per verifica. La classificazione riguarda l’atto nel suo complesso, non la validità di ogni articolo; non deduce abrogazioni parziali. Il codice dell’atto modificante è registrato senza dedurne automaticamente un rapporto di sostituzione. La data del controllo sulla scheda è il riscontro del dettaglio o dell'ultimo evento, non la data del checkpoint tecnico giornaliero.

I decreti ministeriali per cui l'API URN non ha restituito un atto univoco conservano il PDF della fonte istituzionale. Il D.M. 185/2003 dispone di permalink Normattiva, ma il dettaglio API restituisce HTTP 400 ed è escluso dal confronto automatico. I collegamenti PDF ufficiali restano separati dai testi coordinati Normattiva.

## Esecuzione quotidiana e pubblicazione

Gli aggiornamenti su `main` dei file nazionali o della pipeline avviano anche un controllo di riconciliazione dal checkpoint confermato. I push della pipeline con `GITHUB_TOKEN` non generano altri workflow `push`, evitando ricorsioni. La supervisione resta indipendente e non nasconde disallineamenti durante il recupero. Un controllo manuale locale conservato negli audit non sostituisce il checkpoint del branch tecnico: dopo modifiche al registro o allo stato occorre completare l'intera pipeline nazionale.

L'idempotenza giornaliera confronta anche fase, URL dell'esecuzione e impronte della ricevuta con i file correnti: una modifica intervenuta dopo la ricevuta impone un nuovo controllo, anche se le date coincidono. Il test della pre-verifica preserva tutte le sezioni sostanziali sia prima sia dopo la presenza dell'estensione tecnica; non richiede che il registro resti privo di risultati automatici.

La Action nazionale conserva gli avvii alle `07:17`, `08:17` e `09:17` in `Europe/Rome` (ora legale inclusa). I fallback saltano le API soltanto quando checkpoint, stato completato e file pubblici concordano per la giornata. L'avvio manuale può ripetere il controllo. Una programmazione non dimostra un avvio effettivo: il controllo indipendente legge le esecuzioni e i loro step.

La verifica parte dall'ultimo `last_successful_end` confermato, con finestre massime di sette giorni. Gli elenchi paginati vengono suddivisi fino a finestre di un'ora; una risposta ancora incompleta, ambigua o discordante interrompe il controllo. Ogni richiesta ha tre tentativi con attese di uno e due secondi, timeout di 20 secondi e limite complessivo di 120 richieste. Le evidenze delle chiamate e gli errori vengono conservati nell'artifact `normattiva-attempt`, anche quando il job fallisce.

La pubblicazione procede in due fasi. `update-status.json` registra inizialmente `outcome: verificato`, `publication_status: in_attesa`, zero modifiche pubblicate e il precedente risultato valido. Dopo aver confrontato **i byte di national.json e update-status.json serviti da Pages** con i file validati, pubblica la conferma `completato`. Verifica nuovamente i file pubblici e solo allora registra sul ramo `normattiva-state` il checkpoint con ricevuta, hash SHA-256 e URL del workflow. Il deploy attende al massimo 24 verifiche distanziate di dieci secondi, richiedendo una build Pages se necessaria. Un risultato con zero modifiche segue le stesse verifiche.

Il checkpoint resta invariato se interrogazione, pubblicazione o conferma falliscono. Il nuovo tentativo riparte dall'intervallo precedente e recupera gli eventi già pubblicati senza duplicarli, anche quando è fallita soltanto la scrittura del ramo tecnico. I log tecnici conservano al massimo 500 eventi. Le scritture su main confrontano la base nazionale prima di applicare i soli file prodotti; il catalogo territoriale aggiornato da altri processi viene mantenuto. Una modifica nazionale concorrente richiede un nuovo controllo. Il ramo tecnico rifiuta checkpoint più vecchi e fonde gli eventi prima di un nuovo tentativo di push.

## Controllo territoriale e supervisione

Il monitoraggio territoriale esistente è un'attività esterna al repository, configurata alle 10:00 `Europe/Rome`. Utilizza la connessione GitHub autorizzata; le credenziali non sono nel repository. Le fonti istituzionali, la selezione territoriale, la tassonomia e i controlli prima del commit sono definiti nelle sue istruzioni. `data.runs` documenta soltanto le fonti effettivamente lette, gli errori e i limiti. L'esecuzione esterna non è interrogabile dal token della Action: il rapporto non ne certifica autonomamente l'avvio o l'esaustività.

Per i nuovi run, le istruzioni esterne richiedono metadati `execution` con identificativo e orari effettivi, esito `completato/parziale/fallito` e ricevuta di pubblicazione verificata. Un controllo parziale non aggiorna un indicatore di completamento esaustivo. Le cronologie precedenti restano intatte; la presenza di nuove schede non dimostra il completamento di tutte le verifiche. `automation.lastCompletedRun` è un campo storico e non sostituisce la lettura dell'ultimo run documentato.

Non era presente una supervisione indipendente. La nuova Action `monitoring.yml` controlla ogni giorno alle 16:17 `Europe/Rome`, dopo la conclusione della Action nazionale e dopo modifiche territoriali a `data.json`. Legge workflow e step, checkpoint e ricevute, confronta i tre JSON pubblici (fino a tredici letture distanziate di dieci secondi per attendere un deploy in corso) e registra anomalie con identificativi stabili, senza interrogare le fonti normative o modificare i record. Usa un gruppo di concorrenza distinto per non sostituire gli avvii nazionali in attesa; prima di scrivere il solo rapporto verifica che la base non sia cambiata.

La finestra delle 16:00 evita di qualificare come assente un controllo nazionale ancora atteso, considerati gli avvii tardivi osservati. Le letture fallite producono `non_verificabile`, non una presunta assenza. Il rapporto distingue fallimenti, pubblicazione non confermata, disallineamenti, controlli territoriali parziali e indisponibilità ripetute esplicitamente documentate. Le anomalie sostanziali fanno fallire il job dopo la pubblicazione del rapporto; log, summary, artifact e `monitoring-status.json` sono i canali verificabili. Il sito legge facoltativamente il rapporto e mostra gli stati soltanto nella sezione Monitoraggio. Non vengono create notifiche o Issues duplicate.

## Riscontri iniziali dell'8 ottobre 2026

Sono state lette le esecuzioni e i log, non soltanto il loro esito. Il run nazionale [37616626556](https://github.com/domenicoderosa26-web/atlante-idraulico/actions/runs/37616626556), avviato il 7 ottobre alle 13:48:46 locali, ha interrogato realmente Normattiva, trovato zero modifiche, verificato Pages e salvato il checkpoint `2026-10-07T11:48:56Z`. Dal 28 settembre al 7 ottobre risultava un avvio programmato al giorno, tardivo rispetto agli orari configurati; la causa dei ritardi e degli avvii di riserva non presenti nei dati letti non è dimostrata. Non sono stati modificati gli orari sulla base di questa sola osservazione.

La prova API in sola lettura dell'8 ottobre alle 12:43:17 locali ha interrogato l'intervallo `2026-10-07T11:48:56Z`–`2026-10-08T10:43:17Z`, senza modifiche e senza scrivere checkpoint o stati pubblici. L'API copre 11 dei 18 atti del registro: sei decreti senza URN supportato e il D.M. 185/2003 sono esclusi; le rispettive schede e fonti istituzionali rimangono conservate.

L'attività territoriale esterna risulta avviata l'8 ottobre alle 10:13:06 locali. Il run dell'8 ottobre nell'archivio documenta una ricognizione parziale: cinque gruppi di fonti (AUBAC, Po, Sardegna, Bolzano, Sicilia), undici URL letti, otto territori e limiti di accesso. Il campo storico del 25 settembre non certifica l'assenza di esecuzioni successive; anche la ricognizione di quella data documentava accessi inconclusivi. Le prove future di avvio giornaliero non possono essere anticipate da test simulati.

## Verifiche riproducibili

```sh
python scripts/topics.py normalize data.json
python scripts/topics.py validate data.json
python scripts/archive.py --base-ref origin/main
python -m unittest discover -s tests -v
node tests/test_topic_filters.js
```

I test includono risposte API controllate, zero e nuove modifiche, interruzioni, timeout, paginazione incompleta, identità ambigue, recupero e deduplicazione, checkpoint concorrente più recente, confronto byte per byte di Pages, ora legale e inverno, letture tecniche fallite e separazione fra stati nazionali e territoriali. Queste simulazioni non attestano un ciclo futuro né la disponibilità continua delle piattaforme esterne.
