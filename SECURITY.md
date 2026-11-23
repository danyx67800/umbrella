# Security Policy

## Segnalazioni

Non aprire issue pubbliche per vulnerabilità sfruttabili. Usare il reporting
privato di GitHub: **Security → Report a vulnerability** nella pagina del
repository. Il canale è abilitato per questo progetto.

Includere:

- versione Umbrella e tag/commit Chromium (`versions.json`);
- passi di riproduzione e impatto stimato;
- prova di concetto minimizzata, se disponibile;
- eventuali log senza dati personali.

Le vulnerabilità presenti nel motore Chromium vanno segnalate anche al
progetto Chromium secondo la sua policy upstream.

## Ambito

Riguarda le modifiche Umbrella: prefs, integrazione WebUI, nuova scheda,
script di build e packaging. Navigazione, sandbox, Site Isolation, rete,
permessi e rendering sono codice Chromium e seguono le sue tempistiche di
sicurezza.

## Versioni supportate

Il progetto è in sviluppo (0.1.0) e non distribuisce ancora build firmate.
Nessuna versione è dichiarata supportata per uso in produzione.

## Divulgazione

Nessun dettaglio tecnico viene pubblicato prima di una correzione o di un
accordo esplicito con chi ha segnalato. Non vengono promesse protezioni
superiori a quelle effettivamente implementate.

Dettagli su modello di sicurezza e connessioni di rete:
[`docs/SECURITY.md`](docs/SECURITY.md).
