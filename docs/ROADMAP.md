# Roadmap

Stato aggiornato al 23 novembre 2026. Una fase è "fatta" solo se build e test
sono stati eseguiti e registrati; il codice scritto ma non compilato è
"scritto", non "fatto".

## Fase 0 — Analisi e ambiente

| Attività | Stato |
|---|---|
| Analisi architettura Chromium 158 | Fatto |
| Pin tag + commit verificati | Fatto |
| Verifica Git / GitHub CLI / account | Fatto |
| Verifica toolchain Windows | Fatto — **assente** |
| Verifica spazio disco | Fatto — **328 GB, sufficienti** |
| Repository GitHub configurato | Fatto |
| Checkout Chromium locale | Non fatto (bloccato da disco/toolchain) |
| Build Chromium non modificato | Non fatto (bloccato) |

## Fase 1 — Impalcatura fork riproducibile

| Attività | Stato |
|---|---|
| Overlay C++ + WebUI | Scritto, non compilato |
| Specifiche di integrazione con anchor verificati | Fatto |
| Motore check/apply/revert + test | Fatto e testato |
| Script fetch/sync/overlay/build/package | Fatto, non eseguito |
| CI leggera | Fatto |
| Prima build Umbrella | **Bloccata**: mancano VS 2026 + SDK 10.0.28000; installer pronto, UAC non approvato |

Prossimo passo concreto: installare la toolchain (docs/BUILD.md), eseguire
`preflight.py` e `fetch_chromium.py`, poi correggere gli eventuali errori di
compilazione del layer proprietario.

## Fase 2 — Primo browser funzionante

Obiettivo: Umbrella si avvia, naviga, gestisce schede, usa DuckDuckGo, si
chiude senza perdere dati.

- [ ] Build Release `chrome.exe` con overlay
- [ ] Avvio su Windows 10/11 pulito
- [ ] Navigazione HTTP/HTTPS, back/forward/reload/stop
- [ ] Nuova scheda `chrome://umbrella/`
- [ ] DuckDuckGo predefinito e omnibox
- [ ] Chiusura e ripristino sessione
- [ ] Nessuna regressione su Site Isolation/sandbox

## Fase 3 — UI nativa premium

- [ ] Toolbar Views personalizzata (colori, spaziatura, stati)
- [ ] Omnibox: evidenziazione URL al focus, indicatore caricamento
- [ ] Tab strip verticale nativa (riuso `VerticalTabStripStateController`)
- [ ] Sidebar compatta/espansa: schede, preferiti, cronologia, download,
      lista di lettura
- [ ] Drag & drop schede, schede bloccate, ripristino
- [ ] Menu principale e controlli finestra Windows
- [ ] Temi Dark/Light/Auto + accent
- [ ] Animazioni rapide con rispetto di `prefers-reduced-motion`
- [ ] Icone e asset definitivi

## Fase 4 — Funzionalità

- [ ] Preferiti (BookmarkModel) con cartelle, ricerca, barra
- [ ] Cronologia con ricerca e cancellazione per intervallo
- [ ] Download manager personalizzato sul `DownloadManager` nativo
- [ ] Profili multipli e selettore profilo
- [ ] Navigazione privata (OTR) con pulizia alla chiusura
- [ ] Impostazioni complete (`chrome://settings` + sezione Umbrella)
- [ ] Persistenza NTP in pref versionate + export/import
- [ ] Gestione permessi e revoca
- [ ] Estensioni: verifica concreta delle API compatibili

## Fase 5 — Privacy e sicurezza

- [ ] Audit impostazioni: nessuna protezione disattivata
- [ ] Blocco tracker configurabile (liste aggiornabili)
- [ ] Blocco pubblicità con liste di filtri, senza rompere i siti
- [ ] Controllo cookie terze parti documentato
- [ ] Verifica isolamento profili e private mode
- [ ] Documento connessioni di rete effettive

## Fase 6 — Test

- [ ] Matrice siti complessi, video, audio, WebGL, download, popup
- [ ] Session restore, crash recovery, profili, permessi
- [ ] Test su Windows 10 e 11 puliti
- [ ] Nessun test dichiarato senza esito registrato

## Fase 7 — Release

- [ ] Build Release riproducibile
- [ ] Icona, versione, metadati, installer
- [ ] Portable verificata
- [ ] Aggiornamenti firmati (firma crittografica, rollout controllato)
- [ ] Changelog, note, checksum, release `gh`
- [ ] Firma del codice (certificato) prima della distribuzione pubblica

## Non obiettivi

- Compatibilità dichiarata con Chrome Web Store senza verifica.
- Sincronizzazione account proprietaria.
- Telemetria o pubblicità.
- Simulazioni di funzionalità non implementate.
