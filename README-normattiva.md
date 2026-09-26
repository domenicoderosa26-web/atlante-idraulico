# Monitoraggio Normattiva degli atti nazionali

Il sito usa `data.json` per il catalogo esistente e `national.json` come registro supplementare delle 18 schede nazionali. La lettura di quest'ultimo è facoltativa: se non risponde, il catalogo resta utilizzabile. L'aggiornamento territoriale esterno continua a lavorare su `data.json`.

## Fonte e limiti

Le API ufficiali sono documentate da Normattiva in <https://dati.normattiva.it/assets/come_fare_per/API_Normattiva_OpenData.pdf>. Ambiente di produzione: `https://api.normattiva.it/t/normattiva.api`. `POST /bff-opendata/v1/api/v1/ricerca/aggiornati` segnala gli atti aggiornati; `POST /bff-opendata/v1/api/v1/atto/dettaglio-atto-urn` verifica identità e metadati. `POST /bff-opendata/v1/api/v1/ricerca/avanzata` interroga le classi ufficiali 1 (senza aggiornamenti), 2 (aggiornato), 3 (abrogato) con estremi e codice redazionale. Una classificazione ambigua non cambia i dati pubblicati e viene registrata per verifica. La classificazione riguarda l’atto nel suo complesso, non la validità di ogni articolo; non deduce abrogazioni parziali. Il codice dell’atto modificante è registrato senza dedurne automaticamente un rapporto di sostituzione. La data del controllo sulla scheda è il riscontro del dettaglio o dell'ultimo evento, non la data del checkpoint tecnico giornaliero.

I decreti ministeriali per cui l'API URN non ha restituito un atto univoco conservano il PDF della fonte istituzionale. Il D.M. 185/2003 dispone di permalink Normattiva, ma il dettaglio API restituisce HTTP 400 ed è escluso dal confronto automatico. I collegamenti PDF ufficiali restano separati dai testi coordinati Normattiva.

## Esecuzione

La Action `.github/workflows/normattiva.yml` è programmata per le 07:00 in `Europe/Rome`, con due trigger UTC e selezione secondo l'ora legale. Si può avviare manualmente. Il ramo `normattiva-state` conserva `checkpoint.json` (fine dell'ultimo intervallo concluso) ed `events.json` (log tecnico). Il ramo `main` viene aggiornato solo se ci sono modifiche nazionali validate. Al primo avvio si controllano i sette giorni precedenti. La successiva esecuzione riparte dal checkpoint, suddividendo intervalli di sette giorni; se una chiamata fallisce, il checkpoint non avanza e il sito mantiene i dati esistenti. Un errore viene registrato nel log tecnico. Il log è conservato fino agli ultimi 500 eventi.

Test locali: `python -m unittest discover -s tests -v`. Per un controllo effettivo: `python scripts/normattiva.py` dalla radice, con credenziali di scrittura GitHub disponibili alla Action. La Action necessita del permesso `contents: write` per il token del workflow.
