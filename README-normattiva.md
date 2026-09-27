# Monitoraggio Normattiva degli atti nazionali

Il sito usa `data.json` per il catalogo esistente e `national.json` come registro supplementare delle 18 schede nazionali. La lettura di quest'ultimo è facoltativa: se non risponde, il catalogo resta utilizzabile. L'aggiornamento territoriale esterno continua a lavorare su `data.json`.

## Fonte e limiti

Le API ufficiali sono documentate da Normattiva in <https://dati.normattiva.it/assets/come_fare_per/API_Normattiva_OpenData.pdf>. Ambiente di produzione: `https://api.normattiva.it/t/normattiva.api`. `POST /bff-opendata/v1/api/v1/ricerca/aggiornati` segnala gli atti aggiornati; `POST /bff-opendata/v1/api/v1/atto/dettaglio-atto-urn` verifica identità e metadati. `POST /bff-opendata/v1/api/v1/ricerca/avanzata` interroga le classi ufficiali 1 (senza aggiornamenti), 2 (aggiornato), 3 (abrogato) con estremi e codice redazionale. Una classificazione ambigua non cambia i dati pubblicati e viene registrata per verifica. La classificazione riguarda l’atto nel suo complesso, non la validità di ogni articolo; non deduce abrogazioni parziali. Il codice dell’atto modificante è registrato senza dedurne automaticamente un rapporto di sostituzione. La data del controllo sulla scheda è il riscontro del dettaglio o dell'ultimo evento, non la data del checkpoint tecnico giornaliero.

I decreti ministeriali per cui l'API URN non ha restituito un atto univoco conservano il PDF della fonte istituzionale. Il D.M. 185/2003 dispone di permalink Normattiva, ma il dettaglio API restituisce HTTP 400 ed è escluso dal confronto automatico. I collegamenti PDF ufficiali restano separati dai testi coordinati Normattiva.

## Esecuzione quotidiana e pubblicazione

La Action usa `07:17`, `08:17` e `09:17` in `Europe/Rome`. I due avvii di riserva leggono `checkpoint.json`: se il controllo odierno è concluso, terminano senza ripetere le API. `workflow_dispatch` può eseguire un controllo anche nello stesso giorno.

Il controllo scrive `update-status.json` anche con zero modifiche normative. Prima del push valida registro e stato; poi attende la pubblicazione GitHub Pages da `main/(root)`. Se il build automatico non compare, richiede un build tramite API ufficiale. Verifica che Pages serva il medesimo timestamp del risultato prodotto. Soltanto dopo il deploy confermato salva `checkpoint.json` ed `events.json` sul ramo tecnico `normattiva-state`. Un errore non avanza il checkpoint, quindi il successivo tentativo può recuperare l'intervallo. I log sono limitati agli ultimi 500 eventi. Il ramo tecnico viene creato alla prima esecuzione se assente.

Il controllo territoriale resta distinto: non è implementato in questa Action e i suoi esiti non sono attribuiti a Normattiva. Lo stato pubblico di questa Action riguarda esclusivamente la normativa nazionale.

Test locali: `python -m unittest discover -s tests -v`.
