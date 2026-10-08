# Audit documentale — 8 ottobre 2026, lotto 1

**Stato: lotto conservativo validato; Fase 3 complessiva parziale.** Non è una certificazione generale di vigenza e non dichiara completo il censimento nazionale o territoriale.

## Perimetro e risultati

Base: [main 11d0f765](https://github.com/domenicoderosa26-web/atlante-idraulico/commit/11d0f76597bbced47106e6580e39a629140e31cd). Archivio autorevole: `data.json` nella radice. Pages pubblica `main/(root)`; nessuna directory `dist/` è ricreata.

| Indicatore | Prima | Dopo il lotto |
|---|---:|---:|
| Schede normative | 106 | 106 |
| Documenti elencati nelle schede | 138 | 140 |
| Schede con nuova revisione documentale strutturata | 0 | 20 |
| Nuove schede normative | — | 0 |
| Categorie canoniche | 14 | 14 |

Distribuzione iniziale invariata: 18 nazionali, 4 europee, 29 regionali, 13 provinciali, 4 comunali, 3 tecniche, 35 distrettuali. Le 209 URL distinte collegate alle schede iniziali sono state tutte oggetto di richieste: 86 hanno restituito un PDF riconoscibile, 102 un contenuto diverso da PDF, 20 una risposta HTTP diversa da 200 e 1 un timeout. Il totale delle ricevute, aggiungendo permalink/PDF nazionali e fonti documentali mirate, è 228. Sono esiti di accesso, **non** 209 attestazioni di correttezza o vigenza. Le risposte 202/502, pagine vuote, accessi limitati e timeout non provano che un link sia definitivamente rotto.

Il catalogo iniziale contiene 60 stati con formule di verifica/ricostruzione/coordinamento, progetto/adozione, consultazione o storicità (conteggio testuale descrittivo, non una classificazione giuridica). Il confronto documentale circoscritto interessa 20 schede: 3 cataloghi UNI verificati nel perimetro pubblico consentito e 17 revisioni parziali. Per le altre 86 schede è concluso soltanto l’inventario con richieste alle URL: il confronto semantico e giuridico completo resta da svolgere. Nessuna delle 106 schede è qualificata come revisione giuridica esaustiva conclusa.

## Correzioni principali

- **`bz6`**: reperito il [PDF ufficiale della GU Regioni n. 4 del 24 gennaio 2009](https://www.gazzettaufficiale.it/eli/gu/2009/01/24/4/s3/pdf), pp. 17–35. Identificati intestazione e capo IV, artt. 37–47. La GU reca `Omissis` dopo gli articoli: non contiene tutti gli allegati e non è un testo coordinato. Sono riscontrate modifiche successive, fra cui [D.P.P. 22 maggio 2025 n. 9](https://www.gazzettaufficiale.it/eli/id/2026/06/13/25R00323/s3), art. 1 sull’art. 53. Il collegamento è riattivato con etichetta e limiti espliciti; conservate le precedenti cronologie. Lexbrowser ha restituito una pagina di attesa per troppe richieste.
- **`bas9`**: identificati la [GU, atto 17R00266](https://www.gazzettaufficiale.it/eli/id/2017/12/16/17R00266/s3) e il [PDF originario della Regione, quattro pagine](https://www.regione.basilicata.it/wp-content/uploads/giunta/docs/DOCUMENT_FILE_3068771.pdf). Verificati numero, data e artt. 1–8, incluso il rinvio dell’art. 5 alle linee guida. La precedente affermazione generale di vigenza è sostituita con la distinzione tra testo originario identificato e coordinamento ancora da verificare. Il PDF è stato letto nella consultazione testuale iniziale, ma i successivi download diretti hanno restituito errore/timeout: il collegamento conserva `source_link`, non una falsa conferma di download. Non è attestata l’assenza di modifiche legislative.
- **UNI 752, 12056-3, 858-2**: cataloghi ufficiali riportano titolo, data e stato `IN VIGORE` corrispondenti alle schede. Il testo integrale resta soggetto a licenza; nessun PDF non autorizzato viene ricercato o pubblicato.
- **Otto varianti PZP di Bolzano**: confrontati numero/data, Comune, oggetto, componente di pericolosità e dispositivo di approvazione. Confermata la distinzione tra componente idraulica e varianti solo frane/valanghe; nessun tag o territorio è cambiato. Pubblicazione nel Bollettino, efficacia e cartografie restano da acquisire.
- **PAI Po, progetto di estensione, NTA AUBAC, Calabria/Lao, Sardegna e D.G.R. Emilia-Romagna 286/2005**: registrati riscontri di identità/versione/adozione o approvazione effettivamente letti. Per le due varianti sarde sono riscontrate anche le pubblicazioni indicate dall’Autorità (25 giugno e 1 ottobre 2026). Non si estendono questi riscontri all’intera disciplina del bacino né all’assenza di varianti successive.

Le altre 18 schede ricevono evidenze strutturate e una nuova voce di cronologia, senza modificare riferimenti, oggetto, stato, date normative o territorio. Per `bas9` la revisione tassonomica conserva la versione precedente e aggiunge quella della sintesi corretta, con sole fonti istituzionali nella revisione corrente. Categorie e regole non cambiano.

## Evidenze riprendibili

| File | Contenuto |
|---|---|
| [registro-iniziale.json](registro-iniziale.json) | Inventario iniziale delle 106 schede e criticità/limiti registrati prima delle correzioni |
| [schede.json](schede.json) | Esito per ogni ID, aspetti effettivamente riscontrati, perimetro, limiti e verifiche residue |
| [ricevute-url.json](ricevute-url.json) | Richieste, tempi reali, status, destinazione finale, firma PDF, hash ove acquisito e limiti tecnici |
| [consultazioni-documentali.json](consultazioni-documentali.json) | Riscontri testuali istituzionali aggiuntivi, distinti dai download diretti |
| [correzioni.json](correzioni.json) | Valori prima/dopo, motivo/evidenza e conservazione della cronologia per ogni scheda modificata |
| [copertura.json](copertura.json) | Matrice di 20 regioni e 2 Province autonome × 8 materie, con perimetri limitati e attività non iniziate |
| [coda.json](coda.json) | Priorità, ID interessati e candidati non pubblicati come nuove norme |
| [validazione.json](validazione.json) | Conservazione dei dati, file invariati e risultati tecnici del lotto |

Le ricevute registrano la destinazione finale; la sequenza completa dei redirect non è stata raccolta. Questo limite resta esplicito. I documenti scaricati per la lettura non sono duplicati nel repository. I due PDF già presenti in `docs/` sono preservati; hash dei file locali e delle copie pubbliche coincidono. Il testo è estraibile per entrambi, ma questo non ne prova la vigenza attuale. La pagina 17 del PDF GU di Bolzano è stata anche renderizzata e ispezionata.

## Controlli permanenti

`scripts/documentary.py`, richiamato dal validatore dell’archivio, controlla date, perimetro, fonti HTTPS, riscontri puntuali, stato strutturato e limiti delle revisioni. `record_version` lega una revisione a oggetto e fonti della scheda; una variazione richiede un nuovo riesame, conservando la revisione precedente in `documentary_history`. Le nuove dichiarazioni positive di stato, confrontate con `--base-ref`, richiedono evidenza specifica. Le cronologie precedenti non possono essere rimosse. Le schede legacy non modificate rimangono pubblicabili: le lacune del censimento non bloccano un aggiornamento automatico estraneo al loro contenuto.

Questi controlli provano soltanto coerenza dei metadati. Non certificano natura istituzionale, corrispondenza semantica o vigenza di un testo. Le verifiche dei contenuti rimangono documentali. Il monitoraggio territoriale deve leggere [README-documentary.md](../../../README-documentary.md) prima di modificare schede revisionate o dichiarare nuovi stati.

## Validazione e pubblicazione

Superati localmente: normalizzazione e validazione dei 106 record, controllo archivio contro `origin/main`, **55 test Python**, controllo sintattico JavaScript e test del frontend con **14 argomenti A–Z e 168 combinazioni** territorio/livello, ricerca, ordinamento, multiargomento e caricamento dalla radice. I controlli sono ripetuti sulla base aggiornata prima del commit. CI della PR, merge, build Pages e sito pubblico vengono verificati separatamente; il loro esito finale è tracciato nella PR, senza dichiararlo preventivamente in questo documento.

Restano invariati grafica, frontend, filtri, categorie, orari e workflow di monitoraggio, `national.json`, `update-status.json`, checkpoint e registri storici. La supervisione può pubblicare successivamente il proprio rapporto, senza che questo lotto lo sovrascriva.

## Attività residue

La Fase 3 **non è completata**. Restano: confronto semantico/giuridico delle 86 schede senza revisione circoscritta; completamento dei 17 riesami parziali; testo coordinato e allegati Bolzano; coordinamento Basilicata; efficacia/cartografie PZP; rapporti tra vecchi PAI e piani distrettuali; ricerca sistematica degli atti mancanti nelle 20 regioni e Province autonome. Quest’ultima non è ancora avviata nel lotto: si conserva l’ordine audit, criticità, correzioni, censimento. I modificativi emersi durante l’audit sono candidati documentati, non nuove schede incomplete. La matrice non trasforma una richiesta HTTP o la presenza di una scheda in una copertura della materia, e nessuno stato implica assenza di disciplina.

## Prosecuzione incrementale

Il registro [progress.json](../progress.json) raccoglie l'avanzamento dei lotti successivi, con perimetri, limiti e prossime operazioni. Le evidenze storiche di questo audit restano conservate. Il [lotto incrementale 01](incrementale/lotto-01.json) documenta cinque decreti AUBAC: identità, dispositivi e pubblicazioni regionali; gli allegati e la catena successiva restano aperti. Il registro non è un secondo catalogo e i suoi conteggi sono fotografie datate.
