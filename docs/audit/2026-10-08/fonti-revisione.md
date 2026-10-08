# Conservazione delle fonti di revisione — adeguamento tecnico

L’impronta della revisione deve comprendere anche `documentary_review.source_urls`, oltre all’oggetto e ai collegamenti principali/documentali della scheda. La prima implementazione del lotto includeva soltanto questi ultimi: cambiare una fonte aggiuntiva della revisione poteva conservare la medesima impronta. Il controllo ora impedisce questo caso; il semplice riordino delle fonti non cambia la versione.

Le impronte delle 20 revisioni già pubblicate sono migrate al calcolo completo. Ogni revisione precedente è conservata integralmente in `documentary_history`. È un adeguamento tecnico: date di lettura, perimetri, fonti, riscontri, esiti e limiti restano identici. Non è una nuova consultazione documentale. Nessun riferimento, contenuto normativo, argomento o cronologia ordinaria è modificato. L’archivio conserva 106 schede e 20 revisioni correnti.

File dell’adeguamento: `scripts/documentary.py` (calcolo), `tests/test_documentary.py` (regressione), `data.json` (migrazione conservativa), `README-documentary.md` (ordine di calcolo), questo documento (tracciabilità). I registri storici del lotto iniziale rimangono intatti; le vecchie impronte registrate si ritrovano nelle revisioni conservate.

Validazione locale: normalizzazione e validazione degli argomenti, archivio con confronto alla base, 56 test Python, test JavaScript con 14 argomenti e 168 combinazioni, controllo sintattico e diff. CI, merge e confronto dei file pubblicati sono verificati separatamente e il risultato è tracciato nelle PR. L’audit normativo complessivo rimane parziale come dichiarato nel rapporto iniziale.
